RM=rm -f

generate: data.json
	cp favicon.ico docs/
	cp style.css docs/
	./generator.py

clean:
	$(RM) -r docs/*

git:
	git add docs/*
	git add docs/*/*/*

.PHONY: clean git
