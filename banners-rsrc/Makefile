NO_COLOR    = \x1b[0m
BUILD_COLOR    = \x1b[32;01m
CLEAN_COLOR    = \x1b[31;01m


FILES:=$(patsubst %.svg,%.png,$(wildcard *.svg))

	
all: $(FILES)

%.png : %.svg
	@echo -e '$(BUILD_COLOR)* Rendering [$@]$(NO_COLOR)' 
	rsvg-convert $< > $(patsubst %.png,%.png,$@)
	
	
clean:
	@echo -e '$(CLEAN_COLOR)* Cleaning...$(NO_COLOR)' 
	rm -rf $(patsubst %.svg,%.png,$(wildcard *.svg))
	
	
