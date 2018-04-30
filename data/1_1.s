(
(teacher ((name "M Gouttière") (subject ("Math" "Physique"))))
(teacher ((name "Mme Chaudière") (subject ("Français"))))
(teacher ((name "Mme Tardiva") (subject ("Latin"))))
(day_type
    (name normal_week_day)
    (slot (
        (0800 100)
	    (0800 200)
	    (0800 400)
	    (0900 100)
        (1000 100)
        (1000 200)
        (1100 100)
	    (1350 100)
        (1350 200)
        (1350 400)
        (1450 100)
        (1450 200)
        (1450 400)
        (1550 100)
        (1650 100)
        (1650 200)
        (1750 100)
    ))
)
(day_type
    (name half_day)
    (slot (
        (0800 100)
	    (0800 200)
	    (0800 400)
	    (0900 100)
        (1000 100)
        (1000 200)
        (1100 100)
    ))
)

(day (name Lundi) (type normal_week_day))
(day (name Mardi) (type normal_week_day))
(day (name Mercredi)  (type half_day))

(level (name L_2) (subject (Math (200 100)) (Français (100 100))))
(level (name L_1) (subject (Math (200 200)) (Français (100 100))))
(level (name "L_1 latin") (subject (Math (200 200)) (Français (100 100)) (Latin (100))))
(level (name L_0) (subject (Math (200 200 100)) (Français (100 100))))

(group (name "L_2 a") (level L_2))
(group (name "L_2 b") (level L_2))
(group (name "L_1 a") (level "L_1 latin"))
(group (name "L_1 b") (level L_1))
(group (name "L_0 a") (level L_0))

)
