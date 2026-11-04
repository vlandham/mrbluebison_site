# Local preview. Uses mise's Ruby 3.3 (the system Ruby 2.6 is too old for github-pages).
RUBY := mise exec ruby@3.3 --

.PHONY: up install

up: install
	$(RUBY) bundle exec jekyll serve --livereload --open-url

install:
	@$(RUBY) bundle check >/dev/null || $(RUBY) bundle install
