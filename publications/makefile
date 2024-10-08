help:
	@echo "makefile targets"
	@echo "pubs: "

pubs: empty
	fillbib list `cat referee_pub_keys.txt` > referee_pub.bib
	cat header.html > ../publications.html
	btmanip -p referee_pub.bib -html list pubs.html
	cat pubs.html >> ../publications.html
	cat footer.html >> ../publications.html

referee_pub.bib: empty
	fillbib list `cat referee_pub_keys.txt` > referee_pub.bib

other.bib: empty
	fillbib list `cat other_keys.txt`

empty:
