#include <iostream>
#include <memory>

class MyClass {  
public:
    int m_someVariable;   
    int m_badVariableName; 
    
    void SomeFunction() { 
        std::unique_ptr<int> ptr = std::make_unique<int>(42); 
        std::cout << *ptr << std::endl;   
    }
    
    void AnotherFunctionWithVeryLongNameThatExceedsLimit() {  
        int variableWithoutTrailingSpaces = 5;

        std::unique_ptr<char[]> buffer = std::make_unique<char[]>(100);  
    }
};

const int kGlobalConstant = 100;  

void GlobalFunction() {   
    // Function body
}
