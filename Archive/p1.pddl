(define (problem p1) (:domain maze)
(:objects
start goal A B C D E F J H crossA crossB - cell
)

(:init
(= (length start D) 4)
(= (length start C) 2)
(= (length C B) 5)
(= (length D crossA) 0)
(= (length B crossA) 0)
(= (length A crossA) 0)
(= (length crossA B) 5)
(= (length crossA F) 5)
(= (length crossA A) 5)
(= (length B E) 4)
(= (length E crossB) 0)
(= (length A crossB) 0)
(= (length crossB H) 3)
(= (length crossB A) 5)
(= (length crossB E) 4)
(= (length F J) 4)
(= (length J goal) 0)
(= (length H goal) 0)

(can_go start D) 
(can_go start C) 
(can_go C B) 
(can_go D crossA) 
(can_go B crossA) 
(can_go A crossA) 
(can_go crossA B) 
(can_go crossA F) 
(can_go crossA A) 
(can_go B E) 
(can_go E crossB)
(can_go A crossB)
(can_go crossB H)
(can_go crossB A)
(can_go crossB E)
(can_go F J) 
(can_go J goal) 
(can_go H goal) 

(at start)
)

(:goal (at goal))

(:metric minimize (total-cost))
)