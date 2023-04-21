def conc_calc(source_conc, target_conc, target_volume):
    source_add = (target_conc * target_volume) / source_conc
    diluent_add = target_volume - source_add
    return source_add, diluent_add

if __name__ == "__main__":
    source_conc = 30000
    target_conc = 10000
    target_volume = 30

    added_vol = (target_conc * target_volume) / source_conc
    print(added_vol)

    conc_1 = conc_calc(30000, 10000, 30)
    print(conc_1)

    conc_2 = conc_calc(60000, 10000, 30)
    print(conc_2)


