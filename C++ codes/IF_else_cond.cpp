#include<iostream>
using namespace std;

int main() {
    int a = 10;
    int b = 20;
    int c = 30;

    if ((a < b) && (b < c)) {
        cout << "a is less than b and c" << endl;
    } 
    else if ((c > b) && (b > a)) {
        cout << "c is greater" << endl;
    }
    else {
        cout << "b and c are greater than a" << endl;
    }
    
    return 0;
}
