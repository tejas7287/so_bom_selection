/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, xml } from "@odoo/owl";

class PrintBarcodeAction extends Component {
    static template = xml`<t></t>`;

    setup() {
        const url = this.props.action.params?.url;
        if (!url) return;

        fetch(url)
            .then(res => res.text())
            .then(html => {
                // Create a hidden iframe in the current document
                const iframe = document.createElement('iframe');
                iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:1px;height:1px;border:none;';
                document.body.appendChild(iframe);

                const doc = iframe.contentDocument || iframe.contentWindow.document;
                doc.open();
                doc.write(html);
                doc.close();

                // Wait for all resources (images/barcode SVGs) to load
                iframe.contentWindow.onload = () => {
                    iframe.contentWindow.focus();
                    iframe.contentWindow.print();
                    // Remove iframe after print dialog closes
                    setTimeout(() => document.body.removeChild(iframe), 1000);
                };
            });

        // Go back without navigating anywhere
        history.go(-1);
    }
}

registry.category("actions").add("mrp_workorder.print_barcode", PrintBarcodeAction);