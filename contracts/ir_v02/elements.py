"""Element identities only; this list is not a valence model.
Source: IUPAC Periodic Table, 4 May 2022,
https://iupac.org/wp-content/uploads/2022/05/IUPAC_Periodic_Table_A3-04May22.pdf
"""
ELEMENT_SYMBOLS = tuple("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split())
ATOMIC_NUMBERS = {symbol: index + 1 for index, symbol in enumerate(ELEMENT_SYMBOLS)}
