from django.db import models

class AcademicYear(models.Model):
  id = models.AutoField(primary_key=True)
  year_series = models.CharField(max_length=20)
  period = models.CharField(max_length=200)
  status = models.IntegerField(default=0)

  def __str__(self):
    return f"{self.year_series} - {self.period}"


class Students(models.Model):
  id = models.AutoField(primary_key=True)
  academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
  lastname = models.CharField(max_length=200)
  firstname = models.CharField(max_length=200)
  studentid = models.IntegerField(unique=True)

  def __str__(self):
    return str(self.studentid)


class Subject(models.Model):
  id = models.AutoField(primary_key=True)
  subject_name = models.CharField(max_length=50)
  subject_code = models.CharField(max_length=10, null=True)
  subject_pw = models.IntegerField(default=0)
  
  def __str__(self):
    return self.subject_name

class Topic(models.Model):
  id = models.AutoField(primary_key=True)
  subject_topic = models.ForeignKey(Subject, on_delete=models.CASCADE)
  topic_name = models.CharField(max_length=200)

  @property
  def subjectname(self):
    return self.subject_topic.subject_name

  @property
  def subjectcode(self):
    return self.subject_topic.subject_code

  def __str__(self):
    return self.topic_name


class Subtopic(models.Model):
  id = models.AutoField(primary_key=True)
  topic_subtopic = models.ForeignKey(Topic, on_delete=models.CASCADE)
  subtopic_name = models.CharField(max_length=200)

  @property
  def topicname(self):
    return self.topic_subtopic.topic_name

  def __str__(self):
    return self.subtopic_name


class TableOfSpecification(models.Model):
    id = models.AutoField(primary_key=True)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)  
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, null=True, blank=True) 
    subtopic = models.ForeignKey('Subtopic', on_delete=models.CASCADE, null=True, blank=True)

    group_id = models.IntegerField()
    understanding = models.IntegerField(default=0)
    remembering = models.IntegerField(default=0)
    analyzing = models.IntegerField(default=0)
    creating = models.IntegerField(default=0)
    evaluating = models.IntegerField(default=0)
    applying = models.IntegerField(default=0)

    def __str__(self):
        return f"TOS for {self.subject.subject_name} - Topic: {self.topic.topic_name if self.topic else 'N/A'}"

    @property
    def totals_calculated(self):
        return self.understanding + self.remembering + self.analyzing + self.creating + self.evaluating + self.applying


class Category(models.Model):
  id = models.AutoField(primary_key=True)
  category = models.CharField(max_length=50)

  def __str__(self):
    return self.category
  
class Assessment(models.Model):
  id = models.AutoField(primary_key=True)
  academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
  subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
  topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
  competencies = models.ForeignKey(Subtopic, on_delete=models.CASCADE, null=True, blank=True)
  assessment_id = models.IntegerField(null=True, blank=True)

  remembering = models.IntegerField(default=0)
  understanding = models.IntegerField(default=0)
  applying = models.IntegerField(default=0)
  analyzing = models.IntegerField(default=0)
  evaluating = models.IntegerField(default=0)
  creating = models.IntegerField(default=0)

  def __str__(self):
    return str(self.assessment_id)


class Questionnaire(models.Model):
  subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True)
  category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
  topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True)
  subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE, null=True)
  description = models.CharField(max_length=600)
  correct_answer = models.CharField(max_length=200)
  distructor1 = models.CharField(max_length=200)
  distructor2 = models.CharField(max_length=200)
  distructor3 = models.CharField(max_length=200)
  status = models.IntegerField(default=0)
  
  def __str__(self):
    return self.description

class AnswerKeyAssessment(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    question = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE ,null=True, blank=True)
    category = models.CharField(max_length=20, null=True, blank=True)
    assessment_exam_id = models.IntegerField(null=True, blank=True)
    a = models.CharField(max_length=300, null=True, blank=True)
    b = models.CharField(max_length=300, null=True, blank=True)
    c = models.CharField(max_length=300, null=True, blank=True)
    d = models.CharField(max_length=300, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    correct_choice = models.CharField(max_length=1)
    correct_answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.assessment_exam_id)

class AnswerKeyTableOfSpecification(models.Model):
  academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
  tableofspecification = models.ForeignKey(TableOfSpecification, on_delete=models.CASCADE)
  question = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
  subject = models.ForeignKey(Subject, on_delete=models.CASCADE ,null=True, blank=True)
  category = models.CharField(max_length=20, null=True, blank=True)
  number = models.IntegerField(null=True, blank=True)
  tos_exam_id = models.IntegerField(null=True, blank=True)
  a = models.CharField(max_length=300, null=True, blank=True)  
  b = models.CharField(max_length=300, null=True, blank=True)
  c = models.CharField(max_length=300, null=True, blank=True)
  d = models.CharField(max_length=300, null=True, blank=True)
  correct_choice = models.CharField(max_length=1)
  correct_answer = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
      return str(self.tos_exam_id)

class StudentsScoreTos(models.Model):
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(AnswerKeyTableOfSpecification, on_delete=models.CASCADE ,null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    exam_id = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    lastname = models.CharField(max_length=200,null=True, blank=True)
    firstname = models.CharField(max_length=200,null=True, blank=True)
    studentid = models.IntegerField(unique=True,null=True, blank=True)
    period = models.CharField(max_length=200,null=True, blank=True)

    def __str__(self):
      return str(self.studentid)

class StudentsScoreAssessment(models.Model):
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(AnswerKeyAssessment, on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    exam_id = models.IntegerField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    lastname = models.CharField(max_length=200, null=True, blank=True)
    firstname = models.CharField(max_length=200, null=True, blank=True)
    studentid = models.IntegerField(unique=True, null=True, blank=True)
    period = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        unique_together = ['studentid', 'period'] 

    def __str__(self):
        return str(self.studentid)
    

class CategoriesCountPercentage(models.Model):
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, null=True, blank=True)
    remembering = models.IntegerField()
    creating = models.IntegerField()
    understanding = models.IntegerField()
    applying = models.IntegerField()
    analyzing = models.IntegerField()
    evaluating = models.IntegerField()

    remembering_correct_total = models.IntegerField(null=True, blank=True)
    creating_correct_total = models.IntegerField(null=True, blank=True)
    understanding_correct_total = models.IntegerField(null=True, blank=True)
    applying_correct_total = models.IntegerField(null=True, blank=True)
    analyzing_correct_total = models.IntegerField(null=True, blank=True)
    evaluating_correct_total = models.IntegerField(null=True, blank=True)

    @property
    def calculate_remembering_percentage(self):
        return (self.remembering_correct_total / self.remembering) * 100 if self.remembering else 0
    
    @property
    def calculate_creating_percentage(self):
        return (self.creating_correct_total / self.creating) * 100 if self.creating else 0
    
    @property
    def calculate_understanding_percentage(self):
        return (self.understanding_correct_total / self.understanding) * 100 if self.understanding else 0
    
    @property
    def calculate_applying_percentage(self):
        return (self.applying_correct_total / self.applying) * 100 if self.applying else 0
    
    @property
    def calculate_analyzing_percentage(self):
        return (self.analyzing_correct_total / self.analyzing) * 100 if self.analyzing else 0
    
    @property
    def calculate_evaluating_percentage(self):
        return (self.evaluating_correct_total / self.evaluating) * 100 if self.evaluating else 0
    
    def __str__(self):
      return str(self.academic_year)
    


class SubjectCountPercentage(models.Model):
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True)
    total_q_counts_per_subject = models.IntegerField()
    total_correct_counts_per_subject = models.IntegerField()

    def calculate_cor_percentage(self):
        return (self.total_correct_counts_per_subject / self.total_q_counts_per_subject) * 100 if self.total_q_counts_per_subject else 0
    
    def __str__(self):
      return str(self.subject)