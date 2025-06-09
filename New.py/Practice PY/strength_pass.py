# re full form : regular expression
import re
def check_password_strength(password):
    score = 0
    if len(password) >= 8:
        score += 1
    if re.search("[A-Z]", password):
        score += 1
    if re.search("[a-z]", password):
        score += 1
    if re.search("[0-9]", password):
        score += 1
    if re.search("[!@#$%^&*]", password):
        score += 1
    return score
def main():
    password = input("Enter your password: ")
    strength_score = check_password_strength(password)

    print("Password strength score:", strength_score)

    if strength_score == 0:
        print("Password is weak.")
    elif strength_score == 1:
        print("Password is weak improve the strength.")
    elif strength_score == 2:
        print("Password is moderate")
    elif strength_score == 3:
        print("Password is strong.")
    elif strength_score == 4:
        print("Password is very strong.")
if __name__ == "__main__":
   main()

