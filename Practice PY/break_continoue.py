count = 1
while count <= 10:
    print(count)
    count += 1
    if count == 7:
        continue
    print('hi')
    print('exit from loop')

for i in range(1, 12):
    if i == 5:
        break
    else:
        print(i)

