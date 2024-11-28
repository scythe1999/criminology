import json
from django.urls import reverse
from .models import *
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.db.models import Max,Q
import random as rd
from django.db.models import Sum, F
from string import ascii_lowercase
from collections import defaultdict
from django.shortcuts import get_object_or_404, redirect, reverse, render
from .forms import AcademicYearForm
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.exceptions import ValidationError
import pandas as pd
import csv
from django.db import transaction  
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
import logging


total_qty = 0
gnrt_totals = {}
answer_keys = []
answer_keys_tos = []


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)  
            return redirect('homepage')  
        else:
            return render(request, 'authenticate/loginform.html', {'error': 'Invalid username & password'})
    return render(request, 'authenticate/loginform.html')

def logout(request):
    auth_logout(request)
    return redirect('loginpage')


@login_required(login_url='loginpage')
def homepage(request):
    active_year = AcademicYear.objects.filter(status=1).first()
    categoryTos = CategoriesCountPercentage.objects.filter(academic_year=active_year).first()

    enrolled_students_count = Students.objects.filter(academic_year__in=[active_year]).count()

    total = Questionnaire.objects.all().count()
    restrictedquestion = Questionnaire.objects.filter(status=1)
    restricted_counts = Questionnaire.objects.filter(status=1).count()

    restricted_remembering = Questionnaire.objects.filter(status=1, category__category="remembering").count()
    restricted_understanding = Questionnaire.objects.filter(status=1, category__category="understanding").count()
    restricted_creating = Questionnaire.objects.filter(status=1, category__category="creating").count()
    restricted_evaluating = Questionnaire.objects.filter(status=1, category__category="evaluating").count()
    restricted_applying = Questionnaire.objects.filter(status=1, category__category="applying").count()
    restricted_analyzing = Questionnaire.objects.filter(status=1, category__category="analyzing").count()

    if categoryTos:
        percentages = {
            'remembering_percentage': categoryTos.calculate_remembering_percentage,
            'creating_percentage': categoryTos.calculate_creating_percentage,
            'understanding_percentage': categoryTos.calculate_understanding_percentage,
            'applying_percentage': categoryTos.calculate_applying_percentage,
            'analyzing_percentage': categoryTos.calculate_analyzing_percentage,
            'evaluating_percentage': categoryTos.calculate_evaluating_percentage,
        }
    else:
        percentages = {
            'remembering_percentage': 0,
            'creating_percentage': 0,
            'understanding_percentage': 0,
            'applying_percentage': 0,
            'analyzing_percentage': 0,
            'evaluating_percentage': 0,
        }

    subject_count_percentage_data = SubjectCountPercentage.objects.filter(academic_year=active_year)

    subject_data = [
        {
            'subject_code': subject.subject.subject_code,
            'percentage': subject.calculate_cor_percentage()
        }
        for subject in subject_count_percentage_data
    ]

    subject_codes = [data['subject_code'] for data in subject_data]
    subject_percentages = [data['percentage'] for data in subject_data]

    context = {
        'total': total,
        'restrictedquestion': restrictedquestion,
        'restricted_counts': restricted_counts,
        'enrolled_students_count': enrolled_students_count,
        'category': categoryTos,
        'active_year': active_year,
        **percentages,
        'subject_codes': subject_codes,
        'subject_percentages': subject_percentages,
        'restricted_remembering': restricted_remembering,
        'restricted_understanding': restricted_understanding,
        'restricted_creating': restricted_creating,
        'restricted_evaluating': restricted_evaluating,
        'restricted_applying': restricted_applying,
        'restricted_analyzing': restricted_analyzing,
    }

    return render(request, 'assets/dashboard.html', context)




def restrictquestionremove(request, id):

    question = get_object_or_404(Questionnaire, id=id)

    question.status = 0

    question.save()

    return redirect(reverse('restricted_list'))

# ==============QUESTIONNAIRES===============

@login_required(login_url='loginpage')
def questionnaires(request):
    active_academic_year = AcademicYear.objects.filter(status=1).first()

    if active_academic_year is None:
        representative_records = []
        representative_records_assessment = []
        filtered_subjects = Subject.objects.all()
    else:
        subjects = Subject.objects.all()
        category = Category.objects.all()

        existing_entries = TableOfSpecification.objects.filter(academic_year=active_academic_year)
        existing_subject_ids = existing_entries.values_list('subject_id', flat=True)

        filtered_subjects = subjects.exclude(id__in=existing_subject_ids)

        table_of_specification = (
            TableOfSpecification.objects
            .filter(academic_year=active_academic_year)
            .values('group_id')
            .annotate(max_id=Max('id'))
        )

        excluded_group_ids = AnswerKeyTableOfSpecification.objects.values_list('tos_exam_id', flat=True)

        representative_records = TableOfSpecification.objects.filter(
            id__in=[entry['max_id'] for entry in table_of_specification]
        ).exclude(
            group_id__in=excluded_group_ids 
        ).order_by('-id')

        assessment_datas = (
            Assessment.objects
            .filter(academic_year=active_academic_year)
            .values('assessment_id')
            .annotate(max_id=Max('id'))
        )

        representative_records_assessment = Assessment.objects.filter(
            id__in=[entry['max_id'] for entry in assessment_datas]
        ).order_by('-id')

        answer_key_assessment_ids = AnswerKeyAssessment.objects.values_list('assessment_exam_id', flat=True).distinct()
        representative_records_assessment = representative_records_assessment.exclude(
            assessment_id__in=answer_key_assessment_ids
        )

    q = request.GET.get('q', '')

    if q:
        questionnaires = Questionnaire.objects.filter(description__icontains=q).order_by('-id')[:60]
    else:
        questionnaires = Questionnaire.objects.all().order_by('-id')[:60]

    context = {
        'questionnaires': questionnaires,
        'category': category,
        'q': q,
        'table_of_specification': representative_records,
        'assessment': representative_records_assessment
    }

    return render(request, 'assets/questionnaires.html', context)



@login_required(login_url='loginpage')
def questionnairescreate(request):
    subjects = Subject.objects.all()
    category = Category.objects.all()
        
    context = {
        'subjects': subjects,
        'category': category,
    }
    return render(request, 'assets/questionnaires_create.html', context)


def addquestion(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subjectcreate')
        category_id = request.POST.get('categorycreate')
        topic_id = request.POST.get('topiccreate')
        subtopic_id = request.POST.get('subtopiccreate')
        description = request.POST.get('descriptioncreate')
        correct_answer = request.POST.get('correctanscreate')
        distractor1 = request.POST.get('distructorcreate1')
        distractor2 = request.POST.get('distructorcreate2')
        distractor3 = request.POST.get('distructorcreate3')

        subject = Subject.objects.get(id=subject_id)
        category = Category.objects.get(id=category_id)
        topic = Topic.objects.get(id=topic_id)
        subtopic = Subtopic.objects.get(id=subtopic_id)

        datas = Questionnaire.objects.create(
            subject=subject,
            category=category,
            topic=topic,
            subtopic=subtopic,
            description=description,
            correct_answer=correct_answer,
            distructor1=distractor1,
            distructor2=distractor2,
            distructor3=distractor3
        )
        datas.save()
        messages.success(request, 'Added succesfully!')

        return redirect(reverse('questionnairescreate'))
    else:
        pass


def restrictquestion(request, id):
    question = get_object_or_404(Questionnaire, id=id)
    question.status = 1
    question.save()
    messages.success(request, 'Restricted succesfully!')
    return redirect(reverse('questionnaires'))


def delete(request, id):
    q = get_object_or_404(Questionnaire, id=id)
    q.delete()
    return redirect(reverse('questionnaires'))


@login_required(login_url='loginpage')
def update(request, id):
    q = get_object_or_404(Questionnaire, id=id)
    subjects = Subject.objects.all()
    categories = Category.objects.all()
    topics = Topic.objects.filter(subject_topic=q.subject)
    subtopics = Subtopic.objects.filter(topic_subtopic=q.topic)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if 'subject_id' in request.GET:
            subject_id = request.GET.get('subject_id')
            topics = Topic.objects.filter(subject_topic_id=subject_id)
            topics_data = list(topics.values('id', 'topic_name'))
            return JsonResponse({'topics': topics_data})
        elif 'topic_id' in request.GET:
            topic_id = request.GET.get('topic_id')
            subtopics = Subtopic.objects.filter(topic_subtopic_id=topic_id)
            subtopics_data = list(subtopics.values('id', 'subtopic_name'))
            return JsonResponse({'subtopics': subtopics_data})
    
    context = {
        'q': q,
        'subjectsup': subjects,
        'categories': categories,
        'topics': topics,
        'subtopics': subtopics
    }
    return render(request, 'assets/questionnaires_update.html', context)





def updatequestion(request, id):
    if request.method == 'POST':
        try:
            a = request.POST.get('subjectupdate')
            b = request.POST.get('topicupdate')
            c = request.POST.get('subtopicupdate')
            d = request.POST.get('categoryupdate')
            e = request.POST.get('descriptionupdate')
            f = request.POST.get('correctansupdate')
            g = request.POST.get('distructorupdate1')
            h = request.POST.get('distructorupdate2')
            i = request.POST.get('distructorupdate3')

            subject = get_object_or_404(Subject, id=a)
            category = get_object_or_404(Category, id=d)
            topic = get_object_or_404(Topic, id=b)
            subtopic = get_object_or_404(Subtopic, id=c)

            mem = get_object_or_404(Questionnaire, id=id)
            mem.subject = subject
            mem.category = category
            mem.topic = topic
            mem.subtopic = subtopic
            mem.description = e
            mem.correct_answer = f
            mem.distructor1 = g
            mem.distructor2 = h
            mem.distructor3 = i

            mem.save()
            messages.success(request, 'Questionnaire updated successfully!')
            return redirect(reverse('questionnaires'))
        except Exception as ex:
            messages.error(request, f'Error updating questionnaire: {ex}')
            return redirect(reverse('update', args=[id]))
    else:
        return redirect(reverse('update', args=[id]))
    


def get_correct_choice_letter_tos(question, choices):
    for index, choice in enumerate(choices):
        if choice == question.correct_answer:
            return chr(65 + index)  


logger = logging.getLogger(__name__)

def print_questionnaire(request, group_id):
    global answer_keys_tos
    tos_entries = TableOfSpecification.objects.filter(group_id=group_id)

    request.session['group_id'] = group_id

    active_year = AcademicYear.objects.get(status=1)
    generated_questions = []
    answer_keys_tos = []
    category_counts = {category: 0 for category in [
        'understanding',
        'remembering',
        'analyzing',
        'creating',
        'evaluating',
        'applying',
    ]}

    topic_counts = {}
    subject_name = None

    for entry in tos_entries:
        for category in category_counts.keys():
            count = getattr(entry, category)

            subtopic = get_object_or_404(Subtopic, id=entry.subtopic_id)
            topic = get_object_or_404(Topic, id=entry.topic_id)

            try:
                subject = Subject.objects.get(id=entry.subject_id)
            except Subject.DoesNotExist:
                messages.error(request, f"Subject with id {entry.subject_id} does not exist.")
                logger.error(f"Subject with id {entry.subject_id} does not exist.")
                subject = None  

            if subject is not None:
                if subject_name is None:
                    subject_name = subject.subject_name

                if topic.topic_name not in topic_counts:
                    topic_counts[topic.topic_name] = 0

                if category in category_counts:
                    available_questions = Questionnaire.objects.filter(
                        subject=subject,
                        topic=topic,
                        subtopic=subtopic,
                        category__category=category
                    ).order_by('?')[:count]

                    for question in available_questions:
                        choices = [
                            question.correct_answer,
                            question.distructor1,
                            question.distructor2,
                            question.distructor3,
                        ]
                        rd.shuffle(choices)

                        correct_choice_letter = get_correct_choice_letter_tos(question, choices)

                        lettered_choices = [(chr(65 + i), choice) for i, choice in enumerate(choices)]

                        generated_questions.append({
                            'id': question.id,
                            'subject': subject.subject_name,
                            'topic': topic.topic_name,
                            'subtopic': subtopic.subtopic_name,
                            'category': category,
                            'description': question.description,
                            'choices': lettered_choices,
                            'correct_choice_letter': correct_choice_letter,
                            'correct_answer': question.correct_answer,
                        })
                        category_counts[category] += 1
                        topic_counts[topic.topic_name] += 1

                        answer_keys_toss = AnswerKeyTableOfSpecification(
                            academic_year=active_year,
                            tableofspecification=entry,
                            question=question,
                            subject=subject,
                            category=category,
                            number=len(generated_questions),
                            tos_exam_id=group_id,
                            a=lettered_choices[0][1],
                            b=lettered_choices[1][1],
                            c=lettered_choices[2][1],
                            d=lettered_choices[3][1],
                            correct_choice=correct_choice_letter,
                            correct_answer=question.correct_answer,
                        )
                        answer_keys_tos.append(answer_keys_toss)

    primary_keys = [question['id'] for question in generated_questions]
    total_generated_questions = len(generated_questions)

    overall_total = sum(category_counts.values())

    context = {
        'generated_questions': generated_questions,
        'primary_keys': primary_keys,
        'total_generated_questions': total_generated_questions,
        'overall_total': overall_total,
        'category_counts': category_counts,
        'group_id': group_id,
        'subject_name': subject_name, 
        'topic_counts': topic_counts,
    }

    return render(request, 'assets/questionnaire_generate_tos.html', context)

@csrf_exempt
def save_answer_key_tos(answer_keys_tos):
    for answer_key in answer_keys_tos:
        answer_key.save()

def save_answer_key_toss(request):
    global answer_keys_tos

    questions = len(answer_keys_tos)
    group_id = request.session.get('group_id', [])

    if questions == 100:
        save_answer_key_tos(answer_keys_tos)
        answer_keys_tos = []
        return redirect(reverse('questionnaires')) 
    else:
        messages.error(request, "Save failed. Only 100 questions are required to proceed.")
        return redirect(reverse('print_questionnaire', args=[group_id]))

def print_questionnaire_view_table(request, group_id):
    tos_entries = TableOfSpecification.objects.filter(group_id=group_id)
    generated_question_ids = []
    topics = {}

    for entry in tos_entries:
        for category in ['understanding', 'remembering', 'analyzing', 'creating', 'evaluating', 'applying']:
            count = getattr(entry, category)

            subtopic = get_object_or_404(Subtopic, id=entry.subtopic_id)
            topic = get_object_or_404(Topic, id=entry.topic_id)
            subject = get_object_or_404(Subject, id=entry.subject_id)

            available_questions = Questionnaire.objects.filter(
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                category__category=category
            ).order_by('?')[:count]

            for question in available_questions:
                generated_question_ids.append(question.id)

            if topic.id not in topics:
                topics[topic.id] = {
                    'topic_name': topic.topic_name,
                    'totals': {cat: 0 for cat in ['remembering', 'understanding', 'applying', 'analyzing', 'evaluating', 'creating']},
                    'subtopics': {},
                }

            topics[topic.id]['totals'][category] += count 

            if subtopic.id not in topics[topic.id]['subtopics']:
                topics[topic.id]['subtopics'][subtopic.id] = {
                    'subtopic_name': subtopic.subtopic_name,
                    'totals': {cat: 0 for cat in ['remembering', 'understanding', 'applying', 'analyzing', 'evaluating', 'creating']}
                }

            topics[topic.id]['subtopics'][subtopic.id]['totals'][category] += count

    for topic in topics.values():
        topic['total_generated'] = sum(topic['totals'].values())
        for subtopic in topic['subtopics'].values():
            subtopic['total_generated'] = sum(subtopic['totals'].values())

    context = {
        'primary_keys': generated_question_ids,
        'total_generated_questions': len(generated_question_ids),
        'group_id': group_id,
        'topics': topics.values()
    }

    return render(request, 'assets/questionnaire_generate_viewtable_tos.html', context)

def print_assessment(request, assessment_id):
    global answer_keys
    assessments = Assessment.objects.filter(assessment_id=assessment_id)
    active_year = AcademicYear.objects.get(status=1)

    request.session['assessment_id'] = assessment_id 

    answer_keys = []

    generated_questions = []
    category_counts = {
        'remembering': 0,
        'understanding': 0,
        'applying': 0,
        'analyzing': 0,
        'evaluating': 0,
        'creating': 0,
    }

    levels = ['remembering', 'understanding', 'applying', 'analyzing', 'evaluating', 'creating']
    
    answer_data = [] 
    
    question_number = 1 

    for assessment in assessments:
        subject = assessment.subject

        for level in levels:
            num_questions = getattr(assessment, level)

            if num_questions > 0:
                available_questions = Questionnaire.objects.filter(
                    subject=subject,
                    category__category=level,
                    topic=assessment.topic,
                    status=0
                ).order_by('?')[:num_questions]

                for question in available_questions:
                    choices = [
                        question.correct_answer,
                        question.distructor1,
                        question.distructor2,
                        question.distructor3,
                    ]

                    rd.shuffle(choices)
                    correct_choice_letter = get_correct_choice_letter(question, choices)

                    answer_data.append({
                        'assessment_id': assessment_id,
                        'question_id': question.id,
                        'number': question_number,
                        'a': choices[0],
                        'b': choices[1],
                        'c': choices[2],
                        'd': choices[3],
                        'correct_choice': correct_choice_letter,
                        'correct_answer': question.correct_answer,
                    })

                    lettered_choices = [(chr(65 + i), choice) for i, choice in enumerate(choices)]

                    generated_questions.append({
                        'id': question.id,
                        'subject': subject.subject_name,
                        'topic': question.topic.topic_name,
                        'subtopic': question.subtopic.subtopic_name,
                        'category': level,
                        'description': question.description,
                        'choices': lettered_choices,
                        'correct_answer': question.correct_answer,
                    })

                    answer_key = AnswerKeyAssessment(
                        academic_year = active_year,
                        assessment=assessment,
                        question=question,
                        assessment_exam_id=assessment_id,
                        a=lettered_choices[0][1],
                        b=lettered_choices[1][1],
                        c=lettered_choices[2][1],
                        d=lettered_choices[3][1],
                        number=question_number,
                        correct_choice=correct_choice_letter,
                        correct_answer=question.correct_answer,
                        category=level,
                        subject=subject
                    )
                    answer_keys.append(answer_key)

                    category_counts[level] += 1
                    question_number += 1 

    total_generated_questions = len(generated_questions)
    overall_total = sum(category_counts.values())

    context = {
        'generated_questions': generated_questions,
        'total_generated_questions': total_generated_questions,
        'overall_total': overall_total,
        'category_counts': category_counts,
        'assessment_id': assessment_id,
        'subject_name': assessments.first().subject.subject_name,
        'assessments': assessments,
        'answer_data': json.dumps(answer_data),
    }

    return render(request, 'assets/questionnaire_generate_assessment.html', context)

def get_correct_choice_letter(question, choices):
    """ Returns the correct choice letter (A, B, C, or D) based on the correct answer """
    for i, choice in enumerate(choices):
        if choice == question.correct_answer:
            return chr(65 + i)
def save_answer_keys(answer_keys):
    for answer_key in answer_keys:
        answer_key.save()

def save_answer_key(request):
    global answer_keys
    questions = len(answer_keys)
    assessment_id = request.session.get('assessment_id', [])
    
    if questions == 100:
        save_answer_keys(answer_keys)
        answer_keys = []
        return redirect(reverse('questionnaires'))
    else:
        messages.error(request, "Save failed. Only 100 questions are required to proceed.")
        return redirect(reverse('print_assessment', args=[assessment_id]))


def print_questionnaire_view_table_assessment(request, assessment_id):
    assessments = Assessment.objects.filter(assessment_id=assessment_id)
    if not assessments:
        messages.error(request, "No assessments found for the given ID.")
        return redirect(reverse('assessment'))

    
    subjects = Subject.objects.all()

    context = {
        "assessments": assessments,
        "subjects": subjects,
    }

    return render(request, 'assets/questionnaire_generate_viewtable_assessment.html', context)


def get_unique_assessments():
    active_year = AcademicYear.objects.filter(status=1).first()
    assessments = AnswerKeyAssessment.objects.filter(academic_year=active_year).order_by('assessment_exam_id')
    unique_assessments = {}
    for assessment in assessments:
        if assessment.assessment_exam_id not in unique_assessments:
            unique_assessments[assessment.assessment_exam_id] = assessment
    return list(unique_assessments.values())

def get_unique_table_of_specifications():
    active_year = AcademicYear.objects.filter(status=1).first()
    table_of_specifications = AnswerKeyTableOfSpecification.objects.filter(academic_year=active_year).order_by('tos_exam_id')
    unique_tos = {}
    for tos in table_of_specifications:
        if tos.tos_exam_id not in unique_tos:
            unique_tos[tos.tos_exam_id] = tos
    return list(unique_tos.values())

def print_final_nav(request):
    assessment = get_unique_assessments()
    table_of_specification = get_unique_table_of_specifications()

    context = {'assessment': assessment,
               'table_of_specification': table_of_specification}

    return render(request, 'assets/questionnaire_print.html', context)


def print_generated_assessment(request, assessment_exam_id):
    assessment = AnswerKeyAssessment.objects.filter(assessment_exam_id=assessment_exam_id)
    exam_id = assessment.first().assessment_exam_id if assessment.exists() else None
    context = {
        'assessment': assessment,
        'exam_id': exam_id,
        'assessment_exam_id': assessment_exam_id, 
    }

    return render(request, 'assets/questionnaire_print_generated_assessment.html', context)

def print_generated_tableOfSpecification(request, tos_exam_id):
    tos = AnswerKeyTableOfSpecification.objects.filter(tos_exam_id=tos_exam_id)
    exam_id = tos.first().tos_exam_id if tos.exists() else None
    context = {
        'tos': tos,
        'exam_id': exam_id,
        'tos_exam_id': tos_exam_id, 
    }

    return render(request, 'assets/questionnaire_print_generated_tos.html', context)


# ==============MODULES===============

@login_required(login_url='loginpage')
def modulessubject(request):
    subjects = Subject.objects.all().order_by('-id')
    context = {'subjects' : subjects}
    return render(request, 'assets/masterfilesubject.html', context)

@login_required(login_url='loginpage')
def modulestopic(request):
    topics = Topic.objects.all().order_by('-id')
    subjects = Subject.objects.all()
    context = {'topics' : topics,
               'subjects' : subjects}
    return render(request, 'assets/masterfilesubject_topic.html', context)

@login_required(login_url='loginpage')
def modulessubtopic(request):
    subtopic = Subtopic.objects.all().order_by('-id')
    topic = Topic.objects.all()
    context = {'subtopic' : subtopic,
               'topic' : topic}
    return render(request, 'assets/masterfilesubject_subtopic.html', context)

@login_required(login_url='loginpage')
def modules_create_subject(request):
    return render(request, 'partials/modulescreatesubject.html')

@login_required(login_url='loginpage')
def modules_create_topic(request):
    subjects = Subject.objects.all()
    context = {'subjects' : subjects}
    return render(request, 'partials/modulescreatetopic.html',context)

@login_required(login_url='loginpage')
def modules_create_subtopic(request):
    topics = Topic.objects.all()
    context = {'topics' : topics}
    return render(request, 'partials/modulescreatesubtopic.html',context)


def modules_create_subject_final(request):
    if request.method == 'POST':
        subject_name_modules = request.POST.get('subject_name_modules')
        subject_code_modules = request.POST.get('subject_code_modules')
        subject_pw_modules = request.POST.get('subject_pw_modules')

        datas = Subject.objects.create(
            subject_name=subject_name_modules,
            subject_code=subject_code_modules,
            subject_pw=subject_pw_modules,
        )
        datas.save()
        messages.success(request, 'Added succesfully!')
        return redirect(reverse('modulessubject'))
    else:
        pass

def modules_create_topic_final(request):
    if request.method == 'POST':
        subject_topic_modules_id = request.POST.get('subject_topic_modules')
        topic_name_modules = request.POST.get('topic_name_modules')

        subject_topic_modules = get_object_or_404(Subject, id=subject_topic_modules_id)

        datas = Topic.objects.create(
            subject_topic=subject_topic_modules,
            topic_name=topic_name_modules,
        )
        datas.save()
        messages.success(request, 'Added successfully!')
        return redirect(reverse('modulestopic'))
    else:
        pass

def modules_create_subtopic_final(request):
    if request.method == 'POST':
        topic_subtopic_modules_id = request.POST.get('topic_subtopic_modules')
        subtopic_name_modules = request.POST.get('subtopic_name_modules')

        if not topic_subtopic_modules_id or not subtopic_name_modules:
            messages.error(request, 'All fields are required.')
            return redirect(reverse('modules_create_subtopic'))

        try:
            topic_subtopic_modules = get_object_or_404(Topic, id=topic_subtopic_modules_id)
        except Topic.DoesNotExist:
            messages.error(request, 'The specified topic does not exist.')
            return redirect(reverse('modules_create_subtopic'))

        Subtopic.objects.create(
            topic_subtopic=topic_subtopic_modules,
            subtopic_name=subtopic_name_modules,
        )
        messages.success(request, 'Subtopic added successfully!')
        return redirect(reverse('modulessubtopic'))

    return redirect(reverse('modules_create_subtopic'))


@login_required(login_url='loginpage')
def modulessubjectupdate(request, pk):
    subject = get_object_or_404(Subject, id=pk)
    context = {'subject' : subject}
    return render(request, 'assets/masterfilesubjectupdate.html', context)


@login_required(login_url='loginpage')
def modulessubjectdelete(request, pk):
    s = get_object_or_404(Subject, id=pk)
    s.delete()
    return redirect(reverse('modulessubject'))


@login_required(login_url='loginpage')
def modulestopicupdate(request, pk):
    topic = get_object_or_404(Topic, id=pk)
    subjects = Subject.objects.all()
    context = {'topic': topic, 
               'subjects': subjects}
    return render(request, 'assets/masterfilesubject_topicupdate.html', context)


@login_required(login_url='loginpage')
def modulessubtopicupdate(request, pk):
    subtopic = get_object_or_404(Subtopic, id=pk)
    topics = Topic.objects.all()
    context = {'topics': topics, 
               'subtopic': subtopic}
    return render(request, 'assets/masterfilesubject_subtopicupdate.html', context)


def modulessubjectupdatefinal(request, pk):
    if request.method == 'POST':
        
        subjectname = request.POST.get('subject_name_modules')
        subject_code = request.POST.get('subject_code_modules')
        subject_pw = request.POST.get('subject_pw_modules')

        subject = get_object_or_404(Subject, id=pk)

        subject.subject_name = subjectname
        subject.subject_code = subject_code
        subject.subject_pw = subject_pw
        
        subject.save()
        messages.success(request, 'Subject updated successfully!')
        return redirect(reverse('modulessubject'))


@login_required(login_url='loginpage')
def modulestopicupdatefinal(request, pk):
    if request.method == 'POST':
        topicname = request.POST.get('subject_code_modules')
        subject_topic_id = request.POST.get('topic_name_modules')

        topic = get_object_or_404(Topic, id=pk)
        subject_topic = get_object_or_404(Subject, id=subject_topic_id)

        topic.topic_name = topicname
        topic.subject_topic = subject_topic
        
        topic.save()
        messages.success(request, 'Topic updated successfully!')
        return redirect(reverse('modulestopic'))

    return render(request, 'assets/masterfilesubject_topicupdate.html', {'topic': topic, 'subjects': Subject.objects.all()})



def modulestopicdelete(request, pk):
    t = get_object_or_404(Topic, id=pk)
    t.delete()
    return redirect(reverse('modulestopic'))


def modulessubtopicdelete(request, pk):
    s = get_object_or_404(Subtopic, id=pk)
    s.delete()
    return redirect(reverse('modulessubtopic'))



@login_required(login_url='loginpage')
def modulessubtopicupdatefinal(request, pk):
    subtopic = get_object_or_404(Subtopic, id=pk)

    if request.method == 'POST':
        subtopic_name_modules = request.POST.get('subtopic_name_modules')
        topic_subtopic_name_modules = request.POST.get('topic_subtopic_name_modules')

        topic_subtopic = get_object_or_404(Topic, id=topic_subtopic_name_modules)

        subtopic.subtopic_name = subtopic_name_modules
        subtopic.topic_subtopic = topic_subtopic
        
        subtopic.save()
        messages.success(request, 'Subtopic updated successfully!')
        return redirect(reverse('modulessubtopic'))

    return render(request, 'assets/masterfilesubject_subtopicupdate.html', {'subtopic': subtopic, 'topics': Topic.objects.all()})

# ==============MASTERFILE===============


@login_required(login_url='loginpage')
def academic_year(request):
    query = request.GET.get('q')
    if query:
        academic_year = AcademicYear.objects.filter(
            Q(year_series__icontains=query) |
            Q(period__icontains=query)
        ).order_by('-id')
    else:
        academic_year = AcademicYear.objects.all().order_by('-id')

    context = {'academic_year': academic_year}

    return render(request, 'assets/masterfileacademicyear.html', context)


@login_required(login_url='loginpage')
def academicyearcreate(request):
    form = AcademicYearForm()

    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            period = request.POST.get('period')
            status = int(request.POST.get('activestatus')) 

           
            if status == 1:
                
                AcademicYear.objects.filter(status=1).update(status=0)

            new_academic_year = AcademicYear(
                year_series=academic_year,
                period=period,
                status=status
            )
            new_academic_year.save()

            return redirect('academic_year')  
    else:
        form = AcademicYearForm()
    
    context = {'form': form}
    return render(request, 'assets/masterfileacademicyearcreate.html', context)

@login_required(login_url='loginpage')
def academicyearupdate(request, pk):
    academic_year = get_object_or_404(AcademicYear, id=pk)

    if request.method == "POST":
        new_status = int(request.POST.get("activestatusupdate")) 
        new_period = request.POST.get("periodupdate")

        if new_status == 1:
            AcademicYear.objects.filter(status=1).exclude(id=pk).update(status=0)

        academic_year.status = new_status
        academic_year.period = new_period
        academic_year.save()

        messages.success(request, 'Academic year updated successfully!')
        return redirect('academic_year')

    context = {'academic_year': academic_year}
    return render(request, 'assets/masterfileacademicyearupdate.html', context)



@login_required(login_url='loginpage')
def table_of_specification(request):
    query = request.GET.get('q')
    active_academic_year = AcademicYear.objects.filter(status=1).first()
    
    if active_academic_year is None:
        representative_records = []
        filtered_subjects = Subject.objects.all()
    else:
        subjects = Subject.objects.all()
        existing_entries = TableOfSpecification.objects.filter(academic_year=active_academic_year)
        existing_subject_ids = existing_entries.values_list('subject_id', flat=True)
        filtered_subjects = subjects.exclude(id__in=existing_subject_ids)

        if query:
            table_of_specification = (
                TableOfSpecification.objects
                .filter(
                    Q(academic_year=active_academic_year) &
                    (Q(group_id__icontains=query) |
                     Q(subject__subject_name__icontains=query) |
                     Q(topic__topic_name__icontains=query))
                )
                .values('group_id')
                .annotate(max_id=Max('id'))
            )
        else:
            table_of_specification = (
                TableOfSpecification.objects
                .filter(academic_year=active_academic_year)
                .values('group_id')
                .annotate(max_id=Max('id'))
            )
        
        representative_records = TableOfSpecification.objects.filter(id__in=[entry['max_id'] for entry in table_of_specification]).order_by('-id')
    
    context = {'subjects': filtered_subjects, 'table_of_specification': representative_records, 'q': query}
    return render(request, 'assets/masterfiletos.html', context)


def table_of_specification_delete(request, group_id):
    TableOfSpecification.objects.filter(group_id=group_id).delete()
    return redirect(reverse('table_of_secification'))


@login_required(login_url='loginpage')
def table_of_specification_update(request, group_id):
    tos_entries = TableOfSpecification.objects.filter(group_id=group_id).select_related('subtopic', 'topic', 'subject')
    generated_question_ids = []
    topics = {}
    overall_totals = {
        'remembering': 0,
        'understanding': 0,
        'applying': 0,
        'analyzing': 0,
        'evaluating': 0,
        'creating': 0,
    }

    for entry in tos_entries:
        for category in overall_totals.keys():
            count = getattr(entry, category)
            overall_totals[category] += count

            subtopic = entry.subtopic
            topic = entry.topic
            subject = entry.subject

            available_questions = Questionnaire.objects.filter(
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                category__category=category
            ).order_by('?')[:count]

            for question in available_questions:
                generated_question_ids.append(question.id)

            if topic.id not in topics:
                topics[topic.id] = {
                    'topic_name': topic.topic_name,
                    'totals': {cat: 0 for cat in overall_totals.keys()},
                    'subtopics': {},
                }

            topics[topic.id]['totals'][category] += count 

            if subtopic.id not in topics[topic.id]['subtopics']:
                topics[topic.id]['subtopics'][subtopic.id] = {
                    'subtopic_name': subtopic.subtopic_name,
                    'totals': {cat: 0 for cat in overall_totals.keys()}
                }

            topics[topic.id]['subtopics'][subtopic.id]['totals'][category] += count

    for topic in topics.values():
        topic['total_generated'] = sum(topic['totals'].values())
        for subtopic in topic['subtopics'].values():
            subtopic['total_generated'] = sum(subtopic['totals'].values())

    overall_total = sum(overall_totals.values())

    context = {
        'primary_keys': generated_question_ids,
        'total_generated_questions': len(generated_question_ids),
        'group_id': group_id,
        'topics': topics.values(),
        'overall_totals': overall_totals,
        'overall_total': overall_total
    }

    return render(request, 'assets/masterfiletosupdate.html', context)




@login_required(login_url='loginpage')
def table_of_secificationcreate(request, pk):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, id=pk)
        topics = Topic.objects.filter(subject_topic=subject)
        
        group_id = generate_unique_grouptos_id()
        active_academic_year = AcademicYear.objects.filter(status=1).first()

        for topic in topics:
            subtopics = topic.subtopic_set.all()
            for subtopic in subtopics:
                sub_remembering = int(request.POST.get(f'subtopic_remembering_{subtopic.id}', 0))
                sub_understanding = int(request.POST.get(f'subtopic_understanding_{subtopic.id}', 0))
                sub_applying = int(request.POST.get(f'subtopic_applying_{subtopic.id}', 0))
                sub_analyzing = int(request.POST.get(f'subtopic_analyzing_{subtopic.id}', 0))
                sub_evaluating = int(request.POST.get(f'subtopic_evaluating_{subtopic.id}', 0))
                sub_creating = int(request.POST.get(f'subtopic_creating_{subtopic.id}', 0))

                TableOfSpecification.objects.create(
                    academic_year=active_academic_year,
                    subject=subtopic.topic_subtopic.subject_topic,
                    topic=subtopic.topic_subtopic,
                    subtopic=subtopic,
                    group_id=group_id, 
                    remembering=sub_remembering,
                    understanding=sub_understanding,
                    applying=sub_applying,
                    analyzing=sub_analyzing,
                    evaluating=sub_evaluating,
                    creating=sub_creating,
                )

        messages.success(request, "Table of Specification created successfully!")
        return redirect('table_of_secification')

    subject = get_object_or_404(Subject, id=pk)
    topics = Topic.objects.filter(subject_topic=subject).prefetch_related('subtopic_set')
    context = {
        'subject': subject,
        'topics': topics,
    }

    return render(request, 'assets/masterfiletoscreate.html', context)


def table_of_secificationupdate(request, group_id):
    topics = Topic.objects.all().prefetch_related('subtopics')  
    
    if request.method == 'POST':

        for topic in topics:
            for field_name, value in request.POST.items():
                if field_name.startswith(f'subtopic_'): 
                    subtopic_id = field_name.split('_')[2]  
                    subtopic = get_object_or_404(Subtopic, id=subtopic_id)

                    table_of_specification, created = TableOfSpecification.objects.get_or_create(
                        group_id=group_id, subtopic=subtopic, topic=topic
                    )
                    if field_name.endswith('remembering'):
                        table_of_specification.remembering = value
                    elif field_name.endswith('understanding'):
                        table_of_specification.understanding = value
                    elif field_name.endswith('applying'):
                        table_of_specification.applying = value
                    elif field_name.endswith('analyzing'):
                        table_of_specification.analyzing = value
                    elif field_name.endswith('evaluating'):
                        table_of_specification.evaluating = value
                    elif field_name.endswith('creating'):
                        table_of_specification.creating = value
                    table_of_specification.save()

        return redirect('table_of_secification')  


def generate_unique_grouptos_id():
    while True:
        group_id = rd.randint(132414, 199999)
        if not TableOfSpecification.objects.filter(group_id=group_id).exists():
            return group_id





@login_required(login_url='loginpage')
def assessment(request):
    query = request.GET.get('q')
    active_academic_year = AcademicYear.objects.filter(status=1).first()

    if active_academic_year is None:
        representative_records = []
    else:
        if query:
            assessment = (
                Assessment.objects
                .filter(
                    Q(academic_year=active_academic_year) &
                    (Q(assessment_id__icontains=query) |
                     Q(subject__subject_code__icontains=query) |
                     Q(topic__topic_name__icontains=query))
                )
                .values('assessment_id')
                .annotate(max_id=Max('id'))
            )
        else:
            assessment = (
                Assessment.objects
                .filter(academic_year=active_academic_year)
                .values('assessment_id')
                .annotate(max_id=Max('id'))
            )

        representative_records = Assessment.objects.filter(id__in=[entry['max_id'] for entry in assessment]).order_by('-id')

    subjects = Subject.objects.all()
    context = {'subjects': subjects, 'assessment': representative_records, 'q': query}
    return render(request, 'assets/masterfileassessment.html', context)




def generate_unique_assessment_id():
    while True:
        assessment_id = rd.randint(132414, 199999)
        if not Assessment.objects.filter(assessment_id=assessment_id).exists():
            return assessment_id

@login_required(login_url='loginpage')
def assessment_create(request):
    subject = Subject.objects.all()
    assessment_datas = Assessment.objects.all().order_by('-id')

    subject_id = request.POST.get('subjectdropdown_assessment')
    topic_id = request.POST.get('topicdropdown_assessment')
    
    if not subject_id or not topic_id:
        return render(request, 'assets/masterfileassessment_create.html', {
            'error': 'Please select both Subject and Topic.',
            'subject': subject,
        })
    
    try:
        subject_to_table = Subject.objects.get(id=subject_id)
        topic_to_table = Topic.objects.get(id=topic_id)
        subtopics = Subtopic.objects.filter(topic_subtopic=topic_to_table)
        active_academic_year = AcademicYear.objects.filter(status=1).first()
    except Subject.DoesNotExist:
        raise Http404("Subject not found.")
    except Topic.DoesNotExist:
        raise Http404("Topic not found.")
    
    if request.method == "POST":

        assessment_id = generate_unique_assessment_id()
        for subtopic in subtopics:
            remembering = request.POST.get(f'subtopic_remembering_{subtopic.id}', 0)
            understanding = request.POST.get(f'subtopic_understanding_{subtopic.id}', 0)
            applying = request.POST.get(f'subtopic_applying_{subtopic.id}', 0)
            analyzing = request.POST.get(f'subtopic_analyzing_{subtopic.id}', 0)
            evaluating = request.POST.get(f'subtopic_evaluating_{subtopic.id}', 0)
            creating = request.POST.get(f'subtopic_creating_{subtopic.id}', 0)

            assessment = Assessment(
                academic_year=active_academic_year,
                assessment_id=assessment_id,
                subject=subject_to_table,
                topic=topic_to_table,
                competencies=subtopic,
                remembering=remembering,
                understanding=understanding,
                applying=applying,
                analyzing=analyzing,
                evaluating=evaluating,
                creating=creating
            )
            assessment.save()
        
        return redirect('assessment')  
    
    context = {
        'assessment': assessment_datas,
        'subject': subject,
        'topic': topic_to_table,
        'subtopics': subtopics,
    }
    
    return render(request, 'assets/masterfileassessment_create.html', context)


@login_required(login_url='loginpage')
def assessment_update(request, assessment_id):
    assessments_to_update = Assessment.objects.filter(assessment_id=assessment_id)
    if not assessments_to_update:
        messages.error(request, "No assessments found for the given ID.")
        return redirect(reverse('assessment'))

    if request.method == 'POST':
        try:
            for assessment in assessments_to_update:
                remembering = int(request.POST.get(f'remembering_{assessment.id}', '0'))
                understanding = int(request.POST.get(f'understanding_{assessment.id}', '0'))
                applying = int(request.POST.get(f'applying_{assessment.id}', '0'))
                analyzing = int(request.POST.get(f'analyzing_{assessment.id}', '0'))
                evaluating = int(request.POST.get(f'evaluating_{assessment.id}', '0'))
                creating = int(request.POST.get(f'creating_{assessment.id}', '0'))
                
                if any(val < 0 for val in [remembering, understanding, applying, analyzing, evaluating, creating]):
                    raise ValidationError("All values must be non-negative.")

                assessment.remembering = remembering
                assessment.understanding = understanding
                assessment.applying = applying
                assessment.analyzing = analyzing
                assessment.evaluating = evaluating
                assessment.creating = creating
                assessment.save()

            messages.success(request, f'Updated successfully!')
            return redirect(reverse('assessment'))

        except ValueError:
            messages.error(request, "Please enter valid numeric values.")
        except ValidationError as e:
            messages.error(request, str(e))


    subjects = Subject.objects.all()

    context = {
        "assessments_to_update": assessments_to_update,
        "subjects": subjects,
    }

    return render(request, 'assets/masterfileassessment_update.html', context)




def assessment_delete(request, assessment_id):
    q = Assessment.objects.filter(assessment_id=assessment_id)
    q.delete()
    return redirect(reverse('assessment'))




@login_required(login_url='loginpage')
def masterfilestudents(request):
    query = request.GET.get('q')
    active_academic_year = AcademicYear.objects.filter(status=1).first()

    if active_academic_year is None:
        if query:
            students = Students.objects.filter(
                Q(lastname__icontains=query) |
                Q(firstname__icontains=query) |
                Q(studentid__icontains=query)
            ).order_by('-id')
        else:
            students = Students.objects.all().order_by('-id')
    else:
        if query:
            students = Students.objects.filter(
                Q(academic_year=active_academic_year) &
                (Q(lastname__icontains=query) |
                 Q(firstname__icontains=query) |
                 Q(studentid__icontains=query))
            ).order_by('-id')
        else:
            students = Students.objects.filter(academic_year=active_academic_year).order_by('-id')
    
    context = {'students': students, 'q': query}
    return render(request, 'assets/masterfilestudents.html', context)




def export_students(request):
    active_academic_year = AcademicYear.objects.filter(status=1).first()

    if active_academic_year:
        students = Students.objects.filter(academic_year=active_academic_year)
    else:
        students = []

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Last Name', 'First Name', 'Academic Period'])

    for student in students:
        if student.academic_year:
            academic_year = f"{student.academic_year.year_series} - {student.academic_year.period}"
        else:
            academic_year = "N/A"

        writer.writerow([student.studentid, student.lastname, student.firstname, academic_year])

    return response



def generate_unique_student_id():
    while True:
        student_id = rd.randint(132414, 199999)
        if not Students.objects.filter(studentid=student_id).exists():
            return student_id


@login_required(login_url='loginpage')
def masterfilestudentscreate(request):
    academicyear = AcademicYear.objects.filter(status=1)
    studentid = generate_unique_student_id()

    if request.method == 'POST':
        lastname = request.POST.get('lastName')
        firstname = request.POST.get('firstName')
        acadyear_id = request.POST.get('acadyear')

        acadsyear = get_object_or_404(AcademicYear, pk=acadyear_id)

        datas = Students.objects.create(
            lastname=lastname,
            firstname=firstname,
            studentid=studentid,
            academic_year=acadsyear,
        )
        datas.save()
        messages.success(request, 'Student Added!')
        return redirect(reverse('masterfilestudentscreate'))

    context = {'academicyear': academicyear, 'studentid': studentid}
    return render(request, 'assets/masterfilestudentscreate.html', context)



@login_required(login_url='loginpage')
def masterfilestudentsupdate(request, pk):

    student = get_object_or_404(Students, id=pk)

    context = {'student': student}
    
    return render(request, 'assets/masterfilestudentsupdate.html', context)

def deletestudent(request, id):
    q = get_object_or_404(Students, id=id)
    q.delete()
    return redirect(reverse('masterfilestudents'))

    
def masterfilestudentsupdatefinal(request, pk):

    if request.method == 'POST':
        lastname = request.POST.get('lastName_update')
        firstname = request.POST.get('firstName_update')

        students = get_object_or_404(Students, id=pk)

        students.lastname = lastname
        students.firstname = firstname

        students.save()
        messages.success(request, 'Student updated successfully!')
        return redirect(reverse('masterfilestudents'))

# ==============OMR EXAM CHECKER===============

@login_required(login_url='loginpage')
def check_tos(request):
    query = request.GET.get('q', '')
    active_academic_year = AcademicYear.objects.filter(status=1).first()

    representatives = AnswerKeyTableOfSpecification.objects.filter(academic_year=active_academic_year).values('tos_exam_id').distinct()

    representative_entries = []
    for tos_exam in representatives:
        if query:
            representative = AnswerKeyTableOfSpecification.objects.filter(
                Q(academic_year=active_academic_year) &
                Q(tos_exam_id=tos_exam['tos_exam_id']) &
                Q(tos_exam_id__icontains=query)
            ).first()
        else:
            representative = AnswerKeyTableOfSpecification.objects.filter(
                Q(academic_year=active_academic_year) &
                Q(tos_exam_id=tos_exam['tos_exam_id'])
            ).first()
        
        if representative:
            representative_entries.append(representative)

    context = {
        'representative_entries': representative_entries,
        'q': query
    }
    return render(request, "assets/examchecker_tos_check_lists.html", context)



@login_required(login_url='loginpage')
def check_assessment(request):
    query = request.GET.get('q', '')
    active_academic_year = AcademicYear.objects.filter(status=1).first()
    
    representatives = AnswerKeyAssessment.objects.filter(academic_year=active_academic_year).values('assessment_exam_id').distinct()

    representative_entries = []
    for assessment_exam in representatives:
        if query:
            representative = AnswerKeyAssessment.objects.filter(
                Q(academic_year=active_academic_year) &
                Q(assessment_exam_id=assessment_exam['assessment_exam_id']) &
                Q(assessment_exam_id__icontains=query)
            ).first()
        else:
            representative = AnswerKeyAssessment.objects.filter(
                Q(academic_year=active_academic_year) &
                Q(assessment_exam_id=assessment_exam['assessment_exam_id'])
            ).first()
        
        if representative:  # Check to ensure representative is not None
            representative_entries.append(representative)

    context = {
        'representative_entries': representative_entries,
        'q': query
    }
    return render(request, "assets/examchecker_assessment_check_lists.html", context)



def get_representative_exam_ids():
    exam_ids = AnswerKeyTableOfSpecification.objects.values('tos_exam_id').distinct()

    representative_exam_ids = {}
    for exam_id in exam_ids:
        tos_exam_id = exam_id['tos_exam_id']
        representative_exam_id = AnswerKeyTableOfSpecification.objects.filter(tos_exam_id=tos_exam_id).first()
        if representative_exam_id:
            representative_exam_ids[tos_exam_id] = representative_exam_id

    return representative_exam_ids


def import_csv_tos(request, tos_exam_id):
    active_year = AcademicYear.objects.get(status=1)
    exam_id = AnswerKeyTableOfSpecification.objects.filter(tos_exam_id=tos_exam_id).values('tos_exam_id').distinct()
    
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        exam_tos_id = request.POST.get('exam_tos_id')  
        request.session['exam_tos_id'] = exam_tos_id
        
        try:
            data = pd.read_csv(csv_file)

            required_columns = ['ZipGrade ID', 'First Name', 'External Id', 'Last Name', 'Class', 'Num Correct', 'Num Questions']
            question_columns = [col for col in data.columns if col.startswith('Q') and col[1:].isdigit()]
            all_columns = required_columns + question_columns

            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return render(request, "assets/examchecker_tos.html", {
                    "error": f"Missing columns: {', '.join(missing_columns)}",
                    'exam_id': exam_id,
                    'selected_exam_tos_id': exam_tos_id
                })

            data = data.dropna()

            students = Students.objects.all().values('studentid', 'firstname', 'lastname')
            students_df = pd.DataFrame.from_records(students)
            merged_data = pd.merge(data, students_df, left_on='External Id', right_on='studentid')

            question_mapping = {col: int(col[1:]) for col in question_columns}
            for key, value in question_mapping.items():
                merged_data[key] = merged_data[key].apply(lambda x: 1 if x == 1 else 0)

            total_students = len(merged_data)
            passing_threshold = 0.75 * total_students
            restricted_questions = []
            restricted_count_by_category = {category: 0 for category in ['understanding', 'remembering', 'creating', 'evaluating', 'analyzing', 'applying']}

            for question, question_number in question_mapping.items():
                correct_count = merged_data[question].sum()
                if correct_count >= passing_threshold:
                    answer_key_entry = AnswerKeyTableOfSpecification.objects.get(number=question_number, tos_exam_id=tos_exam_id)
                    question_description = answer_key_entry.question.id
                    restricted_questions.append(question_description)

                    if answer_key_entry.category in restricted_count_by_category:
                        restricted_count_by_category[answer_key_entry.category] += 1

            merged_data['Total Score'] = merged_data[question_columns].sum(axis=1)
            merged_data['Rank'] = merged_data['Total Score'].rank(method='dense', ascending=False).astype(int)
            sorted_data = merged_data.sort_values(by='Rank')

            html_table = sorted_data[['Rank', 'First Name', 'Last Name', 'Class', 'Total Score']].to_html(
                classes="table-auto border-collapse border border-gray-400 w-full text-sm text-left", index=False
            ).replace('<td>', '<td class="text-left px-4">').replace('<th>', '<th class="text-left px-4">')

            request.session['sorted_data'] = sorted_data.to_dict('records')
            request.session['restricted_questions'] = restricted_questions
            request.session['restricted_count_by_category'] = restricted_count_by_category
            request.session['tos_exam_id'] = tos_exam_id 

            
            restricted_questions_to_show = Questionnaire.objects.filter(id__in=restricted_questions)

            context = {
                'exam_id': exam_id,
                'scores_table': html_table, 
                'restricted_questions': restricted_questions_to_show, 
                'restricted_count_by_category': restricted_count_by_category,
                'selected_exam_tos_id': exam_tos_id,
                'exam_ids': get_representative_exam_ids(),
            }

            return render(request, "assets/examchecker_tos.html", context)

        except Exception as e:
            return render(request, "assets/examchecker_tos.html", {
                "error": f"An error occurred: {e}",
                'exam_id': exam_id,
                'selected_exam_tos_id': exam_tos_id,
                'exam_ids': get_representative_exam_ids()
            })
    
    selected_exam_tos_id = request.session.get('exam_tos_id', '')  
    
    return render(request, "assets/examchecker_tos.html", {
        'exam_id': exam_id,
        'selected_exam_tos_id': selected_exam_tos_id,
        'exam_ids': get_representative_exam_ids()
    })

def save_data_tos(request):
    if request.method == "POST":
        active_year = AcademicYear.objects.get(status=1)
        sorted_data = request.session.get('sorted_data', [])
        restricted_questions = request.session.get('restricted_questions', [])
        tos_exam_id = request.session.get('tos_exam_id')
        
        for description in restricted_questions:
            Questionnaire.objects.filter(id=description).update(status=1)

        categories = ['understanding', 'remembering', 'creating', 'evaluating', 'analyzing', 'applying']
        category_count = {category: 0 for category in categories}
        correct_count = {f"{category}_correct_total": 0 for category in categories}
        subject_count = {}
        subject_correct_count = {}

        for row in sorted_data:
            student = Students.objects.get(studentid=row['studentid'])
            
            studentscore, created = StudentsScoreTos.objects.update_or_create(
                studentid=student.studentid, 
                academic_year=active_year,
                defaults={
                    'score': row['Total Score'],
                    'rank': row['Rank'],
                    'lastname': row['Last Name'],
                    'firstname': row['First Name'],
                    'period': row['Class'],
                    'exam_id': tos_exam_id,
                }
            )

            question_mapping = {col: int(col[1:]) for col in row.keys() if col.startswith('Q') and col[1:].isdigit()}
            for key, value in question_mapping.items():
                tos = AnswerKeyTableOfSpecification.objects.filter(number=value, tos_exam_id=tos_exam_id).first()
                
                if tos:
                    if tos.subject:
                        subject_id = tos.subject.id
                        studentscore.subject = tos

                        if subject_id not in subject_count:
                            subject_count[subject_id] = 0
                            subject_correct_count[subject_id] = 0
                        subject_count[subject_id] += 1

                        if pd.notna(row[key]) and row[key] == 1:
                            subject_correct_count[subject_id] += 1

                    if tos.category in categories:
                        category_count[tos.category] += 1
                        if pd.notna(row[key]) and row[key] == 1:
                            correct_count[f"{tos.category}_correct_total"] += 1

            studentscore.save()

        for subject_id, total_questions in subject_count.items():
            total_correct = subject_correct_count.get(subject_id, 0)

            existing_subject = SubjectCountPercentage.objects.filter(
                academic_year=active_year, subject_id=subject_id
            ).first()

            if existing_subject:
                existing_subject.total_q_counts_per_subject += total_questions
                existing_subject.total_correct_counts_per_subject += total_correct
                existing_subject.save()
            else:
                SubjectCountPercentage.objects.create(
                    academic_year=active_year,
                    subject_id=subject_id,
                    total_q_counts_per_subject=total_questions,
                    total_correct_counts_per_subject=total_correct,
                )

        total_questions = sum(category_count.values())
        if total_questions == 0:
            total_questions = 1 

        existing_category = CategoriesCountPercentage.objects.filter(academic_year=active_year).first()

        if existing_category:
            existing_category.remembering += category_count.get('remembering', 0)
            existing_category.creating += category_count.get('creating', 0)
            existing_category.understanding += category_count.get('understanding', 0)
            existing_category.applying += category_count.get('applying', 0)
            existing_category.analyzing += category_count.get('analyzing', 0)
            existing_category.evaluating += category_count.get('evaluating', 0)

            existing_category.remembering_correct_total += correct_count.get('remembering_correct_total', 0)
            existing_category.creating_correct_total += correct_count.get('creating_correct_total', 0)
            existing_category.understanding_correct_total += correct_count.get('understanding_correct_total', 0)
            existing_category.applying_correct_total += correct_count.get('applying_correct_total', 0)
            existing_category.analyzing_correct_total += correct_count.get('analyzing_correct_total', 0)
            existing_category.evaluating_correct_total += correct_count.get('evaluating_correct_total', 0)

            existing_category.save()
        else:
            CategoriesCountPercentage.objects.create(
                academic_year=active_year,
                remembering=category_count.get('remembering', 0),
                creating=category_count.get('creating', 0),
                understanding=category_count.get('understanding', 0),
                applying=category_count.get('applying', 0),
                analyzing=category_count.get('analyzing', 0),
                evaluating=category_count.get('evaluating', 0),
                remembering_correct_total=correct_count.get('remembering_correct_total', 0),
                creating_correct_total=correct_count.get('creating_correct_total', 0),
                understanding_correct_total=correct_count.get('understanding_correct_total', 0),
                applying_correct_total=correct_count.get('applying_correct_total', 0),
                analyzing_correct_total=correct_count.get('analyzing_correct_total', 0),
                evaluating_correct_total=correct_count.get('evaluating_correct_total', 0),
            )

        del request.session['sorted_data']
        del request.session['restricted_questions']
        del request.session['tos_exam_id']

        return redirect('check_tos')

def import_csv_assessment(request, assessment_exam_id):
    active_year = AcademicYear.objects.get(status=1)
    exam_id = AnswerKeyAssessment.objects.filter(assessment_exam_id=assessment_exam_id).values('assessment_exam_id').distinct()

    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        exam_assessment_id = request.POST.get('exam_assessment_id')  
        request.session['exam_assessment_id'] = exam_assessment_id 
        
        try:
            data = pd.read_csv(csv_file)

            required_columns = ['ZipGrade ID', 'First Name', 'External Id', 'Last Name', 'Class', 'Num Correct', 'Num Questions']
            question_columns = [col for col in data.columns if col.startswith('Q') and col[1:].isdigit()]
            all_columns = required_columns + question_columns

            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return render(request, "assets/examchecker_assessment.html", {
                    "error": f"Missing columns: {', '.join(missing_columns)}",
                    'exam_id': exam_id,
                    'selected_exam_assessment_id': exam_assessment_id
                })

            data = data.dropna()

            students = Students.objects.all().values('studentid', 'firstname', 'lastname')
            students_df = pd.DataFrame.from_records(students)
            merged_data = pd.merge(data, students_df, left_on='External Id', right_on='studentid')

            question_mapping = {col: int(col[1:]) for col in question_columns}
            
            restricted_questions = []
            restricted_count_by_category = {category: 0 for category in ['understanding', 'remembering', 'creating', 'evaluating', 'analyzing', 'applying']}

            for question, question_number in question_mapping.items():
                correct_count = merged_data[question].sum()
                if correct_count >= 0.75 * len(merged_data):
                    answer_key_entry = AnswerKeyAssessment.objects.get(number=question_number, assessment_exam_id=assessment_exam_id)
                    question_description = answer_key_entry.question.id
                    restricted_questions.append(question_description)

                    if answer_key_entry.category in restricted_count_by_category:
                        restricted_count_by_category[answer_key_entry.category] += 1

            merged_data['Total Score'] = merged_data[question_columns].sum(axis=1)
            merged_data['Rank'] = merged_data['Total Score'].rank(method='dense', ascending=False).astype(int)
            sorted_data = merged_data.sort_values(by='Rank')

            html_table = sorted_data[['Rank', 'First Name', 'Last Name', 'Class', 'Total Score']].to_html(
                classes="table-auto border-collapse border border-gray-400 w-full text-sm text-left", index=False
            ).replace('<td>', '<td class="text-left px-4">').replace('<th>', '<th class="text-left px-4">')

            request.session['sorted_data'] = sorted_data.to_dict('records')
            request.session['restricted_questions'] = restricted_questions
            request.session['restricted_count_by_category'] = restricted_count_by_category
            request.session['assessment_exam_id'] = assessment_exam_id 

            restricted_questions_to_show = Questionnaire.objects.filter(id__in=restricted_questions)
            context = {
                'exam_id': exam_id,
                'scores_table': html_table, 
                'restricted_questions': restricted_questions_to_show, 
                'restricted_count_by_category': restricted_count_by_category,
                'selected_exam_assessment_id': exam_assessment_id,
                'exam_ids': get_representative_exam_ids(),
            }

            return render(request, "assets/examchecker_assessment.html", context)

        except Exception as e:
            return render(request, "assets/examchecker_assessment.html", {
                "error": f"An error occurred: {e}",
                'exam_id': exam_id,
                'selected_exam_assessment_id': exam_assessment_id,
                'exam_ids': get_representative_exam_ids()
            })
    
    selected_exam_assessment_id = request.session.get('exam_assessment_id', '')  
    return render(request, "assets/examchecker_assessment.html", {
        'exam_id': exam_id,
        'selected_exam_assessment_id': selected_exam_assessment_id,
        'exam_ids': get_representative_exam_ids()
    })



def save_data_assessment(request):
    if request.method == "POST":
        active_year = AcademicYear.objects.get(status=1)
        sorted_data = request.session.get('sorted_data', [])
        restricted_questions = request.session.get('restricted_questions', [])
        assessment_exam_id = request.session.get('assessment_exam_id')

        with transaction.atomic():
            try:
                for question_id in restricted_questions:
                    Questionnaire.objects.filter(id=question_id).update(status=1)

                categories = ['understanding', 'remembering', 'creating', 'evaluating', 'analyzing', 'applying']
                category_count = {category: 0 for category in categories}
                correct_count = {f"{category}_correct_total": 0 for category in categories}

                subject_count = {}
                subject_correct_count = {}

                for row in sorted_data:
                    student_score = {
                        'academic_year': active_year,
                        'score': row['Total Score'],
                        'rank': row['Rank'],
                        'lastname': row['Last Name'],
                        'firstname': row['First Name'],
                        'period': row['Class'],
                        'exam_id': assessment_exam_id
                    }

                    print(f"Saving/Updating student: {row['studentid']} with data: {student_score}")
                    student_entry = StudentsScoreAssessment.objects.update_or_create(
                        studentid=row['studentid'],
                        defaults=student_score
                    )

                    student_entry[0].save()
                    print(f"Saved/Updated student: {student_entry[0]}")

                    question_mapping = {col: int(col[1:]) for col in row.keys() if col.startswith('Q') and col[1:].isdigit()}
                    for key, value in question_mapping.items():
                        assessment = AnswerKeyAssessment.objects.filter(number=value, assessment_exam_id=assessment_exam_id).first()
                        
                        if assessment:
                            if assessment.category in categories:
                                category_count[assessment.category] += 1
                                if pd.notna(row[key]) and row[key] == 1: 
                                    correct_count[f"{assessment.category}_correct_total"] += 1

                            if assessment.subject:
                                subject_id = assessment.subject.id
                                if subject_id not in subject_count:
                                    subject_count[subject_id] = 0
                                    subject_correct_count[subject_id] = 0
                                subject_count[subject_id] += 1
                                if pd.notna(row[key]) and row[key] == 1:
                                    subject_correct_count[subject_id] += 1

                                student_entry[0].subject = assessment
                                student_entry[0].save()

                for subject_id, total_questions in subject_count.items():
                    total_correct = subject_correct_count.get(subject_id, 0)

                    existing_subject = SubjectCountPercentage.objects.filter(
                        academic_year=active_year, subject_id=subject_id
                    ).first()

                    if existing_subject:
                        existing_subject.total_q_counts_per_subject += total_questions
                        existing_subject.total_correct_counts_per_subject += total_correct
                        existing_subject.save()
                    else:
                        SubjectCountPercentage.objects.create(
                            academic_year=active_year,
                            subject_id=subject_id,
                            total_q_counts_per_subject=total_questions,
                            total_correct_counts_per_subject=total_correct,
                        )

                total_questions = sum(category_count.values())
                if total_questions == 0:
                    total_questions = 1 

                existing_category = CategoriesCountPercentage.objects.filter(academic_year=active_year).first()

                if existing_category:
                    existing_category.remembering += category_count.get('remembering', 0)
                    existing_category.creating += category_count.get('creating', 0)
                    existing_category.understanding += category_count.get('understanding', 0)
                    existing_category.applying += category_count.get('applying', 0)
                    existing_category.analyzing += category_count.get('analyzing', 0)
                    existing_category.evaluating += category_count.get('evaluating', 0)

                    existing_category.remembering_correct_total += correct_count.get('remembering_correct_total', 0)
                    existing_category.creating_correct_total += correct_count.get('creating_correct_total', 0)
                    existing_category.understanding_correct_total += correct_count.get('understanding_correct_total', 0)
                    existing_category.applying_correct_total += correct_count.get('applying_correct_total', 0)
                    existing_category.analyzing_correct_total += correct_count.get('analyzing_correct_total', 0)
                    existing_category.evaluating_correct_total += correct_count.get('evaluating_correct_total', 0)

                    existing_category.save()
                else:
                    CategoriesCountPercentage.objects.create(
                        academic_year=active_year,
                        remembering=category_count.get('remembering', 0),
                        creating=category_count.get('creating', 0),
                        understanding=category_count.get('understanding', 0),
                        applying=category_count.get('applying', 0),
                        analyzing=category_count.get('analyzing', 0),
                        evaluating=category_count.get('evaluating', 0),
                        remembering_correct_total=correct_count.get('remembering_correct_total', 0),
                        creating_correct_total=correct_count.get('creating_correct_total', 0),
                        understanding_correct_total=correct_count.get('understanding_correct_total', 0),
                        applying_correct_total=correct_count.get('applying_correct_total', 0),
                        analyzing_correct_total=correct_count.get('analyzing_correct_total', 0),
                        evaluating_correct_total=correct_count.get('evaluating_correct_total', 0),
                    )

                del request.session['sorted_data']
                del request.session['restricted_questions']
                del request.session['assessment_exam_id']

                return redirect('check_assessment')

            except IntegrityError as e:
                print(f"IntegrityError: {e}")

                return render(request, "assets/examchecker_assessment.html", {
                    "error": f"An error occurred while saving: {e}",
                    'exam_id': assessment_exam_id,
                })
            except Exception as e:
                print(f"Unexpected error: {e}")
                return render(request, "assets/examchecker_assessment.html", {
                    "error": f"An unexpected error occurred: {e}",
                    'exam_id': assessment_exam_id,
                })



def get_unique_assessments_students_score():
    active_academic_year = AcademicYear.objects.filter(status=1).first()
    
    assessments = StudentsScoreAssessment.objects.filter(academic_year=active_academic_year).order_by('exam_id')
    unique_assessments = {}
    for assessment in assessments:
        if assessment.exam_id not in unique_assessments:
            unique_assessments[assessment.exam_id] = assessment
    return list(unique_assessments.values())

def get_unique_table_of_specifications_students_score():
    active_academic_year = AcademicYear.objects.filter(status=1).first()
    
    table_of_specifications = StudentsScoreTos.objects.filter(academic_year=active_academic_year).order_by('exam_id')
    unique_tos = {}
    for tos in table_of_specifications:
        if tos.exam_id not in unique_tos:
            unique_tos[tos.exam_id] = tos
    return list(unique_tos.values())

def rankings_scores(request):
    assessment = get_unique_assessments_students_score()
    table_of_specification = get_unique_table_of_specifications_students_score()

    context = {'assessment': assessment,
               'table_of_specification': table_of_specification}

    return render(request, 'assets/examchecker_students_ranking.html', context)



def display_scores_assessment(request, exam_id):

    scores = StudentsScoreAssessment.objects.filter(exam_id = exam_id).order_by('rank')
    context = {
        "scores": scores
    }
    return render(request, "assets/examchecker_students_ranking_assessment.html", context)


def display_scores_tos(request, exam_id):

    scores = StudentsScoreTos.objects.filter(exam_id = exam_id).order_by('rank')
    context = {
        "scores": scores
    }
    return render(request, "assets/examchecker_students_ranking_tos.html", context)



@login_required(login_url='loginpage')
def restricted_list(request):
    query = request.GET.get('q', '')
    if query:
        restricted = Questionnaire.objects.filter(
            Q(status=1) &
            (Q(description__icontains=query) |
             Q(subject__subject_code__icontains=query))
        )
    else:
        restricted = Questionnaire.objects.filter(status=1)

    context = {
        "restricted": restricted,
        "q": query
    }
    return render(request, "assets/examchecker_restricted_list.html", context)



# ==============HTMX===============


def subject(request):
    subject_id = request.GET.get('subject')
    topics = Topic.objects.filter(subject_topic_id=subject_id)
    context = {'topics': topics}
    return render(request, 'partials/topic.html', context)

def topic(request):
    topic_id = request.GET.get('topic')
    subtopics = Subtopic.objects.filter(topic_subtopic_id=topic_id)
    context = {'subtopics': subtopics}
    return render(request, 'partials/subtopic.html', context)

def subjectcreate(request):
    subject_id = request.GET.get('subjectcreate')
    topicscreate = Topic.objects.filter(subject_topic_id=subject_id)
    context = {'topicscreate': topicscreate}
    return render(request, 'partials/createquestion.html', context)

def topiccreate(request):
    topic_id = request.GET.get('topiccreate')
    subtopicscreate = Subtopic.objects.filter(topic_subtopic_id=topic_id)
    context = {'subtopicscreate': subtopicscreate}
    return render(request, 'partials/createquestiontopic.html', context)


# ==============AJAX ASSESSMENT===============


def get_topics(request, subject_id):
    try:
        topics = Topic.objects.filter(subject_topic__id=subject_id)
        topic_list = [{'id': topic.id, 'topic_name': topic.topic_name} for topic in topics]
        return JsonResponse({'topics': topic_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_subtopics(request, topic_id):
    try:
        subtopics = Subtopic.objects.filter(topic_subtopic__id=topic_id)
        subtopic_list = [{'id': subtopic.id, 'subtopic_name': subtopic.subtopic_name} for subtopic in subtopics]
        return JsonResponse({'subtopics': subtopic_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

# ==============AJAX LEAVE PAGE===============

def clear_answer_keys_tos(request):
    if request.method == 'POST':
        global answer_keys_tos
        answer_keys_tos = []
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

def clear_answer_keys_assessment(request):
    if request.method == 'POST':
        global answer_keys
        answer_keys = []
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)