frappe.ready(function () {

    const proto = frappe.ui.form.ControlMultiSelectList.prototype;


    const original_make_input = proto.make_input;

    proto.make_input = function () {

        original_make_input.call(this);

        let footer = this.$list_wrapper.find("li.text-right");

        if (footer.length && !footer.find(".select-all-options").length) {

            let btn = $(`
                <button class="btn btn-secondary btn-xs select-all-options mr-2">
                    ${__("Select All")}
                </button>
            `);

            footer.prepend(btn);

            btn.on("click", () => {

                this.values = this._options.map(o => o.value);
                this._selected_values = this._options.slice();

                this.update_status();
                this.set_selectable_items(this._options);

                this.parse_validate_and_set_in_model("");

            });

        }

    };


    

    const original_set_options = proto.set_options;

    proto.set_options = function () {

        let txt = this.$filter_input ? this.$filter_input.val() : "";
        const LIMIT = 200;

        function normalize(options) {
            return (options || []).map(o => ({
                label: o.label || o.value,
                value: o.value,
                description: o.description
            }));
        }

      

        if (this.df.get_data) {

            let result = this.df.get_data(txt);

            if (result && result.then) {

                return result.then(options => {
                    this._options = normalize(options);
                });

            }

            if (Array.isArray(result)) {

                this._options = normalize(result);
                return Promise.resolve();

            }

        }

        
        if (this.df.options && this.df.options !== "Array") {

            return frappe.call({
                method: "frappe.desk.search.search_link",
                args: {
                    doctype: this.df.options,
                    txt: txt,
                    page_length: LIMIT
                }
            }).then(r => {

                this._options = normalize(r.message);

            });

        }

        return original_set_options.call(this);

    };

});
