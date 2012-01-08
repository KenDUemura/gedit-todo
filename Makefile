GEDIT_PLUGIN_DIR = ~/.local/share/gedit/plugins

install:
	@if [ ! -d $(GEDIT_PLUGIN_DIR) ]; then \
		mkdir -p $(GEDIT_PLUGIN_DIR);\
	fi
	@echo "installing todo plugin";
	@rm -rf $(GEDIT_PLUGIN_DIR)/todo*;
	@cp -R todo* $(GEDIT_PLUGIN_DIR);

uninstall:
	@echo "uninstalling todo plugin";
	@rm -rf $(GEDIT_PLUGIN_DIR)/todo*;
