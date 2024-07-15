class MyClass:
    def __init__(self):
        self.public_variable = "I'm a public variable"
        self._protected_variable = "I'm a protected variable"
        self.__private_variable = "I'm a private variable"

    def public_method(self):
        print("This is a public method")

    def _protected_method(self):
        print("This is a protected method")

    def __private_method(self):
        print("This is a private method")

# Creating an instance of MyClass
obj = MyClass()

# Accessing public members
print(obj.public_variable)
obj.public_method()

# Accessing protected members (Convention only)
print(obj._protected_variable)
obj._protected_method()
print(obj._MyClass__private_variable)
obj._MyClass__private_method()

