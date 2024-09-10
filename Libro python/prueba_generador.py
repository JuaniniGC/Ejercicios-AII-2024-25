def mi_generador(n, m, s):
    while(n <= m):
        yield n
        n += s

for n in mi_generador(0, 10, 2):
    print(n)
