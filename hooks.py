# -*- coding: utf-8 -*-


def pre_init_hook(env):
    """
    Runs BEFORE data files load.

    Deletes the broken ir.model.data entry for the report so that Odoo
    recreates it fresh from lot_barcode_report.xml during this upgrade.
    Also fixes report_file on any existing report record.
    """
    # 1. Remove broken xmlid so Odoo recreates it cleanly from XML
    env.cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'so_bom_selection'
           AND name = 'report_lot_barcode'
           AND model = 'ir.actions.report'
    """)

    # 2. Fix report_file on the orphaned report record (if it still exists)
    env.cr.execute("""
        UPDATE ir_act_report_xml
           SET report_file = 'so_bom_selection.report_lot_barcode_template'
         WHERE report_name = 'so_bom_selection.report_lot_barcode'
    """)


def post_init_hook(env):
    """
    Runs AFTER data files load — confirm report_file is correct.
    """
    env.cr.execute("""
        UPDATE ir_act_report_xml
           SET report_file = 'so_bom_selection.report_lot_barcode_template'
         WHERE report_name = 'so_bom_selection.report_lot_barcode'
    """)
    env.cr.execute("SELECT report_file FROM ir_act_report_xml WHERE report_name = 'so_bom_selection.report_lot_barcode'")
    row = env.cr.fetchone()
    if row:
        import logging
        logging.getLogger(__name__).info(
            "[so_bom_selection] report_file after upgrade: %s", row[0]
        )