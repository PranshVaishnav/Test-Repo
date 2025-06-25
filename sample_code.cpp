#include <iostream>
#include <memory>
// Avoid using namespace std in header files, but this is acceptable in .cpp files for demo

class MyClass {  // Fixed: PascalCase for class names
public:
    int m_someVariable;    // Fixed: m_ prefix for member variables
    int m_badVariableName;  // Fixed: m_ prefix and camelCase
    
    void SomeFunction() {  // PascalCase for functions
        std::unique_ptr<int> ptr = std::make_unique<int>(42);  // Fixed: smart pointer
        std::cout << *ptr << std::endl;    // Fixed: std:: prefix and no need for null check with smart pointers
        // No need for manual delete with smart pointers
    }
    
    void AnotherFunctionWithVeryLongNameThatExceedsLimit() {  // Fixed: PascalCase and shortened
        // This line is now within reasonable limits
        int variableWithoutTrailingSpaces = 5;  // Fixed: camelCase

        std::unique_ptr<char[]> buffer = std::make_unique<char[]>(100);  // Fixed: smart pointer array
        // No need for manual free with smart pointers
    }
};

const int kGlobalConstant = 100;  // Fixed: k prefix for constants, PascalCase

void GlobalFunction() {   // Fixed: PascalCase for function names
    // Function body
}
