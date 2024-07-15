#include <iostream>

int main() {
    // Change text color to red
    std::cout << "\033[31mHello, World in Red!\033[0m" << std::endl;

    // Reset to default (though not necessary right after using reset code \033[0m) and print another message
    std::cout << "This is in the default color." << std::endl;

    // Change text color to green
    std::cout << "\033[32mThis text is green!\033[0m" << std::endl;

    // Reset to default and print another message
    std::cout << "This text is in the default color." << std::endl;

    return 0;
}
