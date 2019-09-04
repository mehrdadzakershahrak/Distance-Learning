(define (domain Meeting)
(:requirements :typing)
(:types rover waypoint store camera mode lander objective)

(:predicates (coffee_ready ?j - John)
(have_five_minutes_for_breakfast ?j - John)
(have_five_minutes_for_coffee ?j - John)
(breakfast_ready ?j - John)
(can-move ?start-loc ?end-loc ?t-time)
(have_formall_meeting ?j-John)
(dressed_for_formal-meeting ?j - John)
(have_fifteen_minutes_for_dress ?j - John)
(have_five_minutes_for_lunch ?j - John)
(not_enough_lunch_time ?j - John)
(lunch_packed ?j - John)
(have_five_minutes_for_packlunch ?j - John)
(car_not_works ?j - John)
(at ?start - loc)
(not_have_coffee_beans ?j - John)
(have_fifteen_minutes_for_coffee ?j - John)
(have_twenty_minutes_for_breakfast ?j - John)
(have_ten_minutes_for_dress ?j - John)
(have_twenty_minutes_for_meeting ?j - John)
(meeting_happened ?j-John)
)

(:action make_instant_coffee
:parameters (?j-John )
:precondition (and (not_have_coffee_beans ?j) (have_five_minutes_for_coffee ?j)
	    )
:effect (and (coffee_ready ?j) (not (have_five_minutes_for_coffee ?j))
		)
)

(:action brew_coffee
:parameters (?j-John )
:precondition (and (have_fifteen_minutes_for_coffee ?j)
	    )
:effect (and (coffee_ready ?j) (not (have_fifteen_minutes_for_coffee ?j))
		)
)

(:action eats_small_breakfast
:parameters (?j-John )
:precondition (and (have_five_minutes_for_breakfast ?j)
	    )
:effect (and (breakfast_ready ?j) (not (have_five_minutes_for_breakfast ?j))
		)
)

(:action eats_large_breakfast
:parameters (?j-John )
:precondition (and (have_twenty_minutes_for_breakfast ?j)
	    )
:effect (and (breakfast_ready ?j) (not (have_twenty_minutes_for_breakfast ?j))
		)
)


(:action dress_formally
:parameters (?j-John )
:precondition (and (have_formall_meeting ?j) (have_fifteen_minutes_for_dress ?j)
	    )
:effect (and (dressed_for_formal-meeting ?j) (not (have_fifteen_minutes_for_dress ?j))
		)
)

(:action dress
:parameters (?j-John )
:precondition (and (have_ten_minutes_for_dress ?j)
	    )
:effect (and (not (have_ten_minutes_for_dress ?j))
		)
)


(:action packs_lunch
:parameters (?j-John )
:precondition (and (not_enough_lunch_time ?j) (have_five_minutes_for_lunch ?j)
	    )
:effect (and (lunch_packed ?j) (not (have_five_minutes_for_packlunch ?j))
		)
)

(:action goes
:parameters (?j-John ?t-time ?start-loc ?dest-loc) 
:precondition (and (car_not_works ?j) (at ?start) (can-move ?start ?dest ?t)
	    )
:effect (and (not (at ?start)) (at ?dest)
		)
)

(:action has_formal_meeting
:parameters (?j-John ) 
:precondition (and (have_twenty_minutes_for_meeting ?j) (dressed_for_formal-meeting ?j)
	    )
:effect (and (meeting_happened ?j) (not (have_twenty_minutes_for_meeting ?j))
		)
)

(:action has_meeting
:parameters (?j-John )
:precondition (and (have_twenty_minutes_for_meeting ?j)
	    )
:effect (and (meeting_happened ?j) (not (have_twenty_minutes_for_meeting ?j))
		)
)

(:action has_remote_meeting
:parameters (?j-John ?h-Home)
:precondition (and (have_twenty_minutes_for_meeting ?j) (at ?h)
	    )
:effect (and (meeting_happened ?j) (not (have_twenty_minutes_for_meeting ?j))
		)
)


)
