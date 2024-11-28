from django.contrib import admin
from . models import *

class SubjectAdmin(admin.ModelAdmin):
  list_display = ("subject_name", "subject_code",)
class TopicAdmin(admin.ModelAdmin):
  list_display = ("subject_topic", "topic_name",)
class SubtopicAdmin(admin.ModelAdmin):
  list_display = ("topic_subtopic", "subtopic_name",)
class QuestionnaireAdmin(admin.ModelAdmin):
  list_display = ("description", "category", "correct_answer",)
class AnswerKeyAdmin(admin.ModelAdmin):
  list_display = ("number", "correct_choice","question","correct_answer",)
class AnswerKeyTableOfSpecificationAdmin(admin.ModelAdmin):
  list_display = ("number", "correct_choice","question","correct_answer",)


admin.site.register(Subject,SubjectAdmin)
admin.site.register(Students)
admin.site.register(SubjectCountPercentage)
admin.site.register(CategoriesCountPercentage)
admin.site.register(StudentsScoreTos)
admin.site.register(StudentsScoreAssessment)
admin.site.register(AnswerKeyAssessment,AnswerKeyAdmin)
admin.site.register(AnswerKeyTableOfSpecification,AnswerKeyTableOfSpecificationAdmin)
admin.site.register(TableOfSpecification)
admin.site.register(AcademicYear)
admin.site.register(Assessment)
admin.site.register(Topic,TopicAdmin)
admin.site.register(Subtopic,SubtopicAdmin)
admin.site.register(Category)
admin.site.register(Questionnaire,QuestionnaireAdmin)