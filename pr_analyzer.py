#!/usr/bin/env python3
"""
PR Code Guidelines Analyzer
Analyzes files changed in a GitHub PR for coding guideline violations.
"""

import os
import subprocess
import json
import requests
from typing import List, Dict, Any, Optional
import argparse
from cpp_code_analyzer import CppGuidelinesAnalyzer

class PRAnalyzer:
    """Analyzes PR files for coding guideline violations."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.headers = {}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
    
    def get_pr_changed_files(self, repo_owner: str, repo_name: str, pr_number: int) -> List[str]:
        """Get list of files changed in a PR using GitHub API."""
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            files_data = response.json()
            changed_files = []
            
            for file_info in files_data:
                # Only include files that exist (not deleted)
                if file_info["status"] != "removed":
                    changed_files.append(file_info["filename"])
            
            return changed_files
            
        except requests.RequestException as e:
            print(f"Error fetching PR files: {e}")
            return []
    
    def get_git_changed_files(self, base_branch: str = "main") -> List[str]:
        """Get list of changed files using git diff."""
        try:
            # Get changed files compared to base branch
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            
            changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            
            # Filter to only existing files
            existing_files = [f for f in changed_files if os.path.exists(f)]
            
            return existing_files
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting git changed files: {e}")
            return []
    
    def get_staged_files(self) -> List[str]:
        """Get list of staged files using git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            
            staged_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            existing_files = [f for f in staged_files if os.path.exists(f)]
            
            return existing_files
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting staged files: {e}")
            return []
    
    def analyze_pr_files(self, files: List[str], language: str = "cpp") -> Dict[str, Any]:
        """Analyze files for coding guideline violations."""
        if language.lower() == "cpp":
            analyzer = CppGuidelinesAnalyzer()
            violations = analyzer.analyze_pr_files(files)
            
            return {
                "language": language,
                "files_analyzed": len(files),
                "total_violations": len(violations),
                "violations": violations,
                "summary": {
                    "errors": len([v for v in violations if v.severity == "error"]),
                    "warnings": len([v for v in violations if v.severity == "warning"]),
                    "info": len([v for v in violations if v.severity == "info"])
                }
            }
        else:
            print(f"Language {language} not supported yet")
            return {}
    
    def generate_pr_comment(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a GitHub PR comment with analysis results."""
        if not analysis_result or not analysis_result.get("violations"):
            return "✅ **Code Analysis Complete**\n\nNo coding guideline violations found in the changed files!"
        
        violations = analysis_result["violations"]
        summary = analysis_result["summary"]
        
        comment = "## 📋 Code Analysis Report\n\n"
        comment += f"**Language:** {analysis_result['language'].upper()}\n"
        comment += f"**Files Analyzed:** {analysis_result['files_analyzed']}\n\n"
        
        comment += "### Summary\n"
        comment += f"- 🔴 **Errors:** {summary['errors']}\n"
        comment += f"- 🟡 **Warnings:** {summary['warnings']}\n"
        comment += f"- 🔵 **Info:** {summary['info']}\n\n"
        
        if summary['errors'] > 0:
            comment += "❗ **Please fix the errors before merging.**\n\n"
        
        # Group violations by file
        files_violations = {}
        for violation in violations:
            if violation.file_path not in files_violations:
                files_violations[violation.file_path] = []
            files_violations[violation.file_path].append(violation)
        
        # Show top violations (limit to prevent huge comments)
        max_files = 5
        max_violations_per_file = 10
        
        comment += "### Issues Found\n\n"
        
        for i, (file_path, file_violations) in enumerate(files_violations.items()):
            if i >= max_files:
                remaining_files = len(files_violations) - max_files
                comment += f"... and {remaining_files} more files\n"
                break
                
            comment += f"#### 📁 `{file_path}`\n\n"
            
            # Sort by severity (errors first)
            sorted_violations = sorted(file_violations, 
                                     key=lambda x: {"error": 0, "warning": 1, "info": 2}[x.severity])
            
            for j, violation in enumerate(sorted_violations):
                if j >= max_violations_per_file:
                    remaining = len(sorted_violations) - max_violations_per_file
                    comment += f"... and {remaining} more issues in this file\n\n"
                    break
                    
                icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}[violation.severity]
                comment += f"{icon} **Line {violation.line_number}:** {violation.description}\n"
                
                if violation.suggestion:
                    comment += f"💡 *{violation.suggestion}*\n"
                    
                comment += "\n"
        
        comment += "\n---\n"
        comment += "*This analysis was generated automatically. Please review and address the issues above.*"
        
        return comment


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze PR files for coding guideline violations")
    parser.add_argument("--pr", help="GitHub PR in format 'owner/repo/pr_number'")
    parser.add_argument("--files", nargs="+", help="Specific files to analyze")
    parser.add_argument("--git-diff", help="Compare against branch (default: main)", 
                       nargs="?", const="main")
    parser.add_argument("--staged", action="store_true", help="Analyze staged files")
    parser.add_argument("--language", default="cpp", help="Programming language (default: cpp)")
    parser.add_argument("--format", choices=["text", "json", "pr-comment"], 
                       default="text", help="Output format")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--github-token", help="GitHub token for API access")
    
    args = parser.parse_args()
    
    analyzer = PRAnalyzer(args.github_token)
    files_to_analyze = []
    
    # Determine which files to analyze
    if args.pr:
        # Parse PR format: owner/repo/pr_number
        pr_parts = args.pr.split('/')
        if len(pr_parts) != 3:
            print("PR format should be: owner/repo/pr_number")
            return
        
        owner, repo, pr_num = pr_parts
        files_to_analyze = analyzer.get_pr_changed_files(owner, repo, int(pr_num))
        print(f"Found {len(files_to_analyze)} changed files in PR #{pr_num}")
        
    elif args.git_diff is not None:
        files_to_analyze = analyzer.get_git_changed_files(args.git_diff)
        print(f"Found {len(files_to_analyze)} changed files compared to {args.git_diff}")
        
    elif args.staged:
        files_to_analyze = analyzer.get_staged_files()
        print(f"Found {len(files_to_analyze)} staged files")
        
    elif args.files:
        files_to_analyze = args.files
        
    else:
        print("Please specify files to analyze using --files, --pr, --git-diff, or --staged")
        return
    
    if not files_to_analyze:
        print("No files to analyze")
        return
    
    # Analyze the files
    analysis_result = analyzer.analyze_pr_files(files_to_analyze, args.language)
    
    # Generate output
    if args.format == "json":
        # Convert violations to dict for JSON serialization
        violations_data = []
        for v in analysis_result.get("violations", []):
            violations_data.append({
                "rule_name": v.rule_name,
                "description": v.description,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "line_content": v.line_content,
                "severity": v.severity,
                "suggestion": v.suggestion
            })
        
        output = {
            "language": analysis_result.get("language"),
            "files_analyzed": analysis_result.get("files_analyzed"),
            "total_violations": analysis_result.get("total_violations"),
            "summary": analysis_result.get("summary"),
            "violations": violations_data
        }
        
        output_text = json.dumps(output, indent=2)
        
    elif args.format == "pr-comment":
        output_text = analyzer.generate_pr_comment(analysis_result)
        
    else:  # text format
        if analysis_result.get("violations"):
            cpp_analyzer = CppGuidelinesAnalyzer()
            output_text = cpp_analyzer.generate_report(analysis_result["violations"], "text")
        else:
            output_text = "✅ No coding guideline violations found!"
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
        print(f"Analysis saved to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main() 