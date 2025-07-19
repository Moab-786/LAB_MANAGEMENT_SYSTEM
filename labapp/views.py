from django.shortcuts import render, redirect
from .forms import StudentForm
from .models import Component, Student, IssueRecord, ReturnRecord
from django.utils import timezone
from django.utils.timezone import now
import subprocess, json
from django.shortcuts import render, get_object_or_404
from yolo_detect import live_detection
from django.shortcuts import render, redirect, get_object_or_404
from .models import Component, Student, IssueRecord, ReturnRecord
from django.utils.timezone import now
from django.db import models

def live_auto_issue(request):
    student_id = request.session.get('current_student_id')
    if not student_id:
        return redirect('student_form')
    student = get_object_or_404(Student, id=student_id)

    detected_counts = live_detection("media/my_model.pt", "media/vid.mp4", 0.8, (1280, 720), display=True)
    if detected_counts is None:
        detected_counts = {}

    detected_components = []
    for name, count in detected_counts.items():
        component_data = {"name": name, "quantity": count}
        try:
            component = Component.objects.get(name__iexact=name)
            issued_qty = IssueRecord.objects.filter(
                student=student, component=component, returned=False
            ).aggregate(total_issued_qty=models.Sum('quantity_issued'))['total_issued_qty'] or 0

            qty_to_issue = count - issued_qty

            if qty_to_issue > 0:
                if component.quantity_available >= qty_to_issue:
                    component.quantity_available -= qty_to_issue
                    component.save()
                    IssueRecord.objects.create(
                        student=student,
                        component=component,
                        quantity_issued=qty_to_issue
                    )
                    component_data["status"] = f"Issued {qty_to_issue}"
                else:
                    component_data["status"] = "Insufficient Stock"
            else:
                component_data["status"] = "Already Issued"

        except Component.DoesNotExist:
            component_data["status"] = " Not in DB"
        detected_components.append(component_data)

    return render(request, "issue_auto.html", {
        "student": student,
        "detected_components": detected_components
    })

def live_auto_return(request):
    student_id = request.session.get('current_student_id')
    if not student_id:
        return redirect('student_form')
    student = get_object_or_404(Student, id=student_id)

    detected_counts = live_detection("media/my_model.pt", "media/vid.mp4", 0.8, (1280, 720), display=True)
    if detected_counts is None:
        detected_counts = {}

    detected_returns = []
    for name, count in detected_counts.items():
        component_data = {"name": name, "quantity": count}
        try:
            component = Component.objects.get(name__iexact=name)
            # Calculate unreturned quantity for this component and student
            unreturned_issues = IssueRecord.objects.filter(
                student=student, component=component, returned=False
            )
            total_unreturned_qty = unreturned_issues.aggregate(total_qty=models.Sum('quantity_issued'))['total_qty'] or 0

            # Calculate quantity to return (minimum of detected count and unreturned quantity)
            qty_to_return = min(count, total_unreturned_qty)

            if qty_to_return > 0:
                # Return the quantity by creating ReturnRecords for unreturned issues
                remaining_qty = qty_to_return
                for issue in unreturned_issues:
                    if remaining_qty <= 0:
                        break
                    issue_qty = issue.quantity_issued
                    if issue_qty <= remaining_qty:
                        ReturnRecord.objects.create(
                            issue=issue,
                            condition="Working",
                            date_returned=now()
                        )
                        issue.returned = True
                        issue.save()
                        component.quantity_available += issue_qty
                        component.save()
                        remaining_qty -= issue_qty
                    else:
                        # Partial return not handled, can be extended if needed
                        break
                component_data["status"] = f"Returned {qty_to_return}"
            else:
                component_data["status"] = "❌ Not Issued or Already Returned"
        except Component.DoesNotExist:
            component_data["status"] = "❌ Not Found in DB"
        detected_returns.append(component_data)

    return render(request, "return_auto.html", {
        "student": student,
        "returned_components": detected_returns
    })


def student_form(request):
    initial = {}
    # Use GET params for initial values if present
    if request.method == 'GET':
        name = request.GET.get('name')
        roll_number = request.GET.get('roll_number')
        course = request.GET.get('course')
        if name:
            initial['name'] = name
        if roll_number:
            initial['roll_number'] = roll_number
        if course:
            initial['course'] = course

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            roll = form.cleaned_data['roll_number']
            name = form.cleaned_data['name']
            course = form.cleaned_data['course']

            # Get or create the student by roll number
            student, _ = Student.objects.get_or_create(
                roll_number=roll,
                defaults={'name': name, 'course': course}
            )

            # Store student data in session
            request.session['current_student_id'] = student.id
            request.session['success_student_name'] = student.name
            request.session['success_student_roll'] = student.roll_number
            request.session['success_student_course'] = student.course  # <-- Add this line

            action = request.POST.get('action')  # 'issue' or 'return'
            return redirect(f'/dashboard/{action}/')
    else:
        form = StudentForm(initial=initial)

    return render(request, 'student_form.html', {'form': form})


def component_dashboard(request, action):
    if action not in ['issue', 'return']:
        return redirect('student_form')
    
    components = Component.objects.all()
    return render(request, 'dashboard.html', {
        'components': components,
        'action': action
    })


def issue_form(request):
    components = Component.objects.all()
    student_id = request.session.get('current_student_id')

    if not student_id:
        return redirect('student_form')

    student = Student.objects.get(id=student_id)

    if request.method == 'POST':
        total = int(request.POST.get('total', 0))
        issued_summary = []

        for i in range(total):
            if request.POST.get(f'selected_{i}') == 'on':
                comp_id = request.POST.get(f'component_id_{i}')
                qty = request.POST.get(f'quantity_{i}')

                if comp_id and qty:
                    try:
                        component = Component.objects.get(id=comp_id)
                        quantity_issued = int(qty)
                        # Check if already issued and not returned
                        already_issued = IssueRecord.objects.filter(
                            student=student, component=component, returned=False
                        ).exists()
                        if already_issued:
                            status = "Already Issued"
                        elif component.quantity_available >= quantity_issued:
                            component.quantity_available -= quantity_issued
                            component.save()
                            IssueRecord.objects.create(
                                student=student,
                                component=component,
                                quantity_issued=quantity_issued,
                                date_issued=timezone.now(),
                                returned=False
                            )
                            status = f"Issued {quantity_issued}"
                        else:
                            status = "Insufficient Stock"
                        issued_summary.append({
                            "name": component.name,
                            "quantity": quantity_issued,
                            "status": status
                        })
                    except Component.DoesNotExist:
                        issued_summary.append({
                            "name": f"ID {comp_id}",
                            "quantity": qty,
                            "status": "Not Found"
                        })

        request.session['issued_components'] = issued_summary
        request.session['success_student_name'] = student.name
        request.session['success_student_roll'] = student.roll_number
        request.session['success_student_course'] = student.course  # <-- Add this line
        request.session['return_component'] = []
        return redirect('success')

    return render(request, 'issue_form.html', {
        'components': components,
        'student': student
    })


def return_form(request):
    components = Component.objects.all()
    student_id = request.session.get('current_student_id')

    if not student_id:
        return redirect('student_form')

    student = Student.objects.get(id=student_id)

    if request.method == 'POST':
        total = int(request.POST.get('total', 0))
        returned_summary = []

        for i in range(total):
            if request.POST.get(f'selected_{i}') == 'on':
                comp_id = request.POST.get(f'component_id_{i}')
                qty = request.POST.get(f'quantity_{i}')

                if comp_id and qty:
                    try:
                        component = Component.objects.get(id=comp_id)
                        quantity_returned = int(qty)
                        issued_qty = IssueRecord.objects.filter(
                            student=student, component=component, returned=False
                        ).aggregate(total_issued_qty=models.Sum('quantity_issued'))['total_issued_qty'] or 0

                        if issued_qty == 0:
                            status = "Not Issued or Already Returned"
                        elif issued_qty >= quantity_returned and quantity_returned > 0:
                            component.quantity_available += quantity_returned
                            component.save()
                            # Mark as returned in IssueRecord and create ReturnRecord
                            issues = IssueRecord.objects.filter(
                                student=student, component=component, returned=False
                            )
                            remaining = quantity_returned
                            for issue in issues:
                                if remaining <= 0:
                                    break
                                if issue.quantity_issued <= remaining:
                                    # Create ReturnRecord for this issue
                                    ReturnRecord.objects.create(
                                        issue=issue,
                                        condition="Working",  # Or get from form if you want
                                        date_returned=now()
                                    )
                                    issue.returned = True
                                    issue.save()
                                    remaining -= issue.quantity_issued
                                else:
                                    # Partial return not handled, can be extended
                                    break
                            status = f"Returned {quantity_returned}"
                        else:
                            status = "Return Quantity Exceeds Issued"
                        returned_summary.append({
                            "name": component.name,
                            "quantity": quantity_returned,
                            "status": status
                        })
                    except Component.DoesNotExist:
                        returned_summary.append({
                            "name": f"ID {comp_id}",
                            "quantity": qty,
                            "status": "Not Found"
                        })

        request.session['return_component'] = returned_summary
        request.session['issued_components'] = []
        return redirect('success')

    return render(request, 'return_form.html', {
        'components': components,
        'student': student
    })


def success(request):
    # Determine last action based on which list is not empty
    issued = request.session.get('issued_components', [])
    returned = request.session.get('return_component', [])
    if issued and len(issued) > 0:
        action = 'issue'
    else:
        action = 'return'
    return render(request, 'success.html', {
        'student_name': request.session.get('success_student_name', ''),
        'student_roll': request.session.get('success_student_roll', ''),
        'student_course': request.session.get('success_student_course', ''),  # Add this line
        'issued_components': issued,
        'return_component': returned,
        'action': action,
    })


def admin_report(request):
    return render(request, 'admin_report.html')
