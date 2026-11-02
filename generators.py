def my_generator(max_val):
    count = 1
    flag = True

    while True:
        if flag == True and count < max_val:
            yield count
            count += 1
        elif flag == True and count == max_val:
            flag = False
        elif flag == False and count > 0 :
            yield count
            count -= 1
        elif flag == False and count == 0:
            flag = True


def lch(x0, a, c, m, count=None):
    xn = x0
    step = 0
    while True:
        if count is not None and step == count:
            return
        
        xn = (a * xn + c) % m
        yield xn
        step += 1  


if __name__ == "__main__":
    for i in lch(1, 3, 5, 8, 30):
        print(i, end=", ")

    print()
    for index, i in enumerate(lch(1, 5, 3, 8)):
        if index >= 10:
            break
        print(i, end=", ")


#for i in my_generator(10):
#    print(i)
#
