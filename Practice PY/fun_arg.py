def school (name,subj,depart):
    print(f"hi {name}")
    print(f"do you teach {subj}")
    print(f"are you from which depart {depart}")
school ("srinu","python","computer science depart",)


def add (*num):
    c=0
    for i in num:
        c=c+i
    print(f"sum of{c}")

add (3,4,5)
add (5,6,7,8)

def add (*num,name):
    c=0
    print(num)
    print(name)
    for i in num:
        c=c+i
    print(f"sum is {c}")
add(45,67,name="jenny")
add (1,0,-1)

def add2 (a,b):
    c=a+b
    return c
    print(c)
add2(3,3)






