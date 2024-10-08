help:
	@echo "Makefile targets"
	@echo "---------------------------------------------------"
	@echo "pubs: Create 'publications.html' from the keys in  "
	@echo "      referee_pub_keys.txt."

pubs: empty
	fillbib list `cat referee_pub_keys.txt` > referee_pub.bib
	cat header.html > ../publications.html
	btmanip -p referee_pub.bib -html list pubs.html
	cat pubs.html >> ../publications.html
	cat footer.html >> ../publications.html
	/home/awsteiner/bin/rep "<li>" "<li style=\"text-align: left;\">" \
		../publications.html

replace:
	/home/awsteiner/bin/rep "<li>" "<li style=\"text-align: left;\">" \
		../publications.html

referee_pub.bib: empty
	fillbib list `cat referee_pub_keys.txt` > referee_pub.bib

other.bib: empty
	fillbib list `cat other_keys.txt`

empty:
