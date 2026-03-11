frappe.ui.form.ControlMultiSelectList = class ControlMultiSelectList extends (
	frappe.ui.form.ControlData
) {

	static trigger_change_on_input_event = false;

	make_input() {

		let template = `
			<div class="multiselect-list dropdown">
				<div class="form-control cursor-pointer input-xs" data-toggle="dropdown" tabindex=0>
					<div class="status-text ellipsis"></div>
				</div>
				<ul class="dropdown-menu">
					<li class="dropdown-input-wrapper">
						<input type="text" class="form-control input-xs">
					</li>
					<div class="selectable-items"></div>
					<li class="d-flex justify-content-end">
						<button class="btn btn-secondary btn-xs select-all-options text-nowrap mr-2">
							${__("Select All")}
						</button>
						<button class="btn btn-primary btn-xs clear-selections text-nowrap">
							${__("Clear All")}
						</button>
					</li>
				</ul>
			</div>
		`;

		this.$list_wrapper = $(template);
		this.$input = $("<input>");
		this.input = this.$input.get(0);
		this.has_input = true;

		this.$list_wrapper.prependTo(this.input_area);
		this.$filter_input = this.$list_wrapper.find("input");

		this.values = [];
		this._options = [];
		this._selected_values = [];
		this.highlighted = -1;

		this.$list_wrapper.on("click", ".dropdown-menu", (e) => {
			e.stopPropagation();
		});

		this.$list_wrapper.on("click", ".clear-selections", () => {
			this.clear_all_selections();
		});

		this.$list_wrapper.on("click", ".select-all-options", () => {
			this.select_all_options();
		});

		this.$list_wrapper.on("click", ".selectable-item", (e) => {
			let $target = $(e.currentTarget);
			this.toggle_select_item($target);
		});

		this.$list_wrapper.on(
			"input",
			"input",
			frappe.utils.debounce((e) => {

				this.set_options().then(() => {

					let txt = e.target.value;

					let filtered_options = this._options.filter((opt) => {

						if (this.values.includes(opt.value)) return true;

						return (
							Awesomplete.FILTER_CONTAINS(opt.label, txt) ||
							Awesomplete.FILTER_CONTAINS(opt.value, txt) ||
							Awesomplete.FILTER_CONTAINS(opt.description, txt)
						);
					});

					let options = this._selected_values
						.concat(filtered_options)
						.uniqBy((opt) => opt.value);

					this.set_selectable_items(options);
				});

			}, 300)
		);

		this.$list_wrapper.on("show.bs.dropdown", () => {

			this.set_options().then(() => {

				if (!this._selected_values || !this._selected_values.length) {
					this._selected_values = this.process_options(this.values);
				}

				this._options = this._selected_values
					.concat(this._options)
					.uniqBy((opt) => opt.value);

				this.set_selectable_items(this._options);
			});
		});

		this.set_input_attributes();
	}

	set_input_attributes() {

		this.$list_wrapper
			.attr("data-fieldtype", this.df.fieldtype)
			.attr("data-fieldname", this.df.fieldname);

		this.set_status(this.get_placeholder_text());
	}

	clear_all_selections() {

		this.values = [];
		this._selected_values = [];

		this.update_status();
		this.set_selectable_items(this._options);

		this.parse_validate_and_set_in_model("");

		if (frappe.query_report) {
			frappe.query_report.refresh();
		}
	}

	select_all_options() {

		this.values = this._options.map((opt) => opt.value);
		this._selected_values = this._options.slice();

		this.update_status();
		this.set_selectable_items(this._options);

		this.parse_validate_and_set_in_model("");

		if (frappe.query_report) {
			frappe.query_report.refresh();
		}
	}

	toggle_select_item($item) {

		$item.toggleClass("selected");

		let value = decodeURIComponent($item.data().value);

		if ($item.hasClass("selected")) {
			this.values.push(value);
		} else {
			this.values = this.values.filter((val) => val !== value);
		}

		this.parse_validate_and_set_in_model("");
		this.update_status();

		if (frappe.query_report) {
			frappe.query_report.refresh();
		}
	}

	update_status() {

		let text;

		if (this.values.length === 0) {
			text = this.get_placeholder_text();
		}
		else if (this.values.length === 1) {
			text = this.values[0];
		}
		else {
			text = `${this.values.length} values selected`;
		}

		this.set_status(text);
	}

	get_placeholder_text() {
		return `<span class="text-extra-muted">${this.df.placeholder || ""}</span>`;
	}

	set_status(text) {
		this.$list_wrapper.find(".status-text").html(text);
	}

	process_options(options) {

		return options.map((option) => {

			if (typeof option === "string") {
				return { label: option, value: option };
			}

			if (!option.label) option.label = option.value;

			return option;
		});
	}

	set_options() {

		let promise = Promise.resolve();

		if (this.df.get_data) {

			let txt = this.$filter_input.val();
			let value = this.df.get_data(txt);

			if (!value) {
				this._options = [];
			}
			else if (value.then) {

				promise = value.then((options) => {
					this._options = this.process_options(options);
				});
			}
			else {
				this._options = this.process_options(value);
			}
		}
		else {
			this._options = this.process_options(this.df.options);
		}

		return promise;
	}

	set_selectable_items(options) {

		let html = options.map((option) => {

			let encoded = encodeURIComponent(option.value);
			let selected = this.values.includes(option.value) ? "selected" : "";

			return `
				<li class="selectable-item ${selected}" data-value="${encoded}">
					<div>
						<strong>${option.label}</strong>
					</div>
					<div class="multiselect-check">
						${frappe.utils.icon("tick","xs")}
					</div>
				</li>
			`;

		}).join("");

		if (!html) {
			html = `<li class="text-muted">${__("No values to show")}</li>`;
		}

		this.$list_wrapper.find(".selectable-items").html(html);
	}

	get_value() {
		return this.values;
	}
};



/* GLOBAL REPORT FILTER SUPPORT */

frappe.after_ajax(() => {

	if (!frappe.query_report || !frappe.query_report.filters) return;

	frappe.query_report.filters.forEach(filter => {

		if (!filter || !filter.df) return;

		if (filter.df.fieldtype !== "MultiSelectList") return;

		filter.df.get_data = function (txt) {

			let doctype = filter.df.options;

			if (filter.df.fieldname === "party") {

				doctype = frappe.query_report.get_filter_value("party_type");

				if (!doctype) return [];
			}

			let args = {
				doctype: doctype,
				txt: txt,
				page_length: "200"
			};

			if (["account","cost_center"].includes(filter.df.fieldname)) {

				args.filters = {
					company: frappe.query_report.get_filter_value("company")
				};
			}

			return frappe.call({
				method: "frappe.desk.search.search_link",
				args: args
			}).then(r => r.message);
		};

	});

});
