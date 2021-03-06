# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EducationStudentsAttendance(models.Model):
    _name = 'education.attendance'

    name = fields.Char(string='Name', default='New')
    class_id = fields.Many2one('education.class', string='Class')
    division_id = fields.Many2one('education.class.division', string='Division', required=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    attendance_line = fields.One2many('education.attendance.line', 'attendance_id', string='Attendance Line')
    attendance_created = fields.Boolean(string='Attendance Created')
    all_marked_morning = fields.Boolean(string='All students are present in the morning')
    all_marked_afternoon = fields.Boolean(string='All students are present in the afternoon')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    academic_year = fields.Many2one('education.academic.year', string='Academic Year',
                                    related='division_id.academic_year_id', store=True)
    faculty_id = fields.Many2one('education.faculty', string='Faculty')

    @api.model
    def create(self, vals):
        res = super(EducationStudentsAttendance, self).create(vals)
        res.class_id = res.division_id.class_id.id
        attendance_obj = self.env['education.attendance']
        already_created_attendance = attendance_obj.search(
            [('division_id', '=', res.division_id.id), ('date', '=', res.date), ('company_id', '=', res.company_id.id)])
        if len(already_created_attendance) > 1:
            raise ValidationError(
                _('Attendance register of %s is already created on "%s"', ) % (res.division_id.name, res.date))
        return res

    @api.multi
    def create_attendance_line(self):
        self.name = str(self.date)
        attendance_line_obj = self.env['education.attendance.line']
        students = self.division_id.student_ids
        if len(students) < 1:
            raise UserError(_('There are no students in this Division'))
        for student in students:
            data = {
                'name': self.name,
                'attendance_id': self.id,
                'student_id': student.id,
                'roll_no': student.roll_no,
                'student_name': student.name,
                'class_id': self.division_id.class_id.id,
                'division_id': self.division_id.id,
                'date': self.date,
            }
            attendance_line_obj.create(data)
        self.attendance_created = True

    @api.multi
    def mark_all_present_morning(self):
        for records in self.attendance_line:
            records.present_morning = True
        self.all_marked_morning = True

    @api.multi
    def un_mark_all_present_morning(self):
        for records in self.attendance_line:
            records.present_morning = False
        self.all_marked_morning = False

    @api.multi
    def mark_all_present_afternoon(self):
        for records in self.attendance_line:
            records.present_afternoon = True
        self.all_marked_afternoon = True

    @api.multi
    def un_mark_all_present_afternoon(self):
        for records in self.attendance_line:
            records.present_afternoon = False
        self.all_marked_afternoon = False

    @api.multi
    def attendance_done(self):
        for records in self.attendance_line:
            records.state = 'done'
            if not records.present_morning and not records.present_afternoon:
                records.full_day_absent = 1
            elif not records.present_morning:
                records.half_day_absent = 1
            elif not records.present_afternoon:
                records.half_day_absent = 1
            else:
                records.full_day_absent = 0
        self.state = 'done'

    @api.multi
    def set_to_draft(self):
        for records in self.attendance_line:
            records.state = 'draft'
        self.state = 'draft'


class EducationAttendanceLine(models.Model):
    _name = 'education.attendance.line'
    _order='roll_no asc'

    name = fields.Char(string='Name')
    attendance_id = fields.Many2one('education.attendance', string='Attendance Id')
    roll_no=fields.Integer('Roll No')
    student_id = fields.Many2one('education.student', string='Student')
    student_name = fields.Char(string='Student', related='student_id.name', store=True)
    class_id = fields.Many2one('education.class', string='Class', required=True)
    division_id = fields.Many2one('education.class.division', string='Division', required=True)
    date = fields.Date(string='Date', required=True)
    present_morning = fields.Boolean(string='Morning')
    present_afternoon = fields.Boolean(string='After Noon')
    full_day_absent = fields.Integer(string='Full Day')
    half_day_absent = fields.Integer(string='Half Day')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State', default='draft')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    academic_year = fields.Many2one('education.academic.year', string='Academic Year',
                                    related='division_id.academic_year_id', store=True)
