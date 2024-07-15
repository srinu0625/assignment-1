# include<iostream>
using namespace std;
int main()
{
    int a,b,c=0;
    cout<<"enter a num :";
    cin>>a;
    cout<<"enter a num :";
    cin>>b;
    cout<<"binary oper(num+num):"<<a+b<<"\n";
    cout<<"ternary oper"<<((a>b)?a:b)<<"\n";
    cout<<"relational oper(num+num):"<<(a<b)<<"\n";
    cout<<"assignment oper:sum:"<<(c+=a)<<"\n";
    cout<<"logical oper"<<(true&&false)<<"\n";
    return 0;
}