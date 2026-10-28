from django.db import models


class Exam(models.Model):
    title = models.CharField('título', max_length=200)
    description = models.TextField('descripción', blank=True)
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'examen'
        verbose_name_plural = 'exámenes'
        ordering = ['id']

    def __str__(self):
        return self.title


class Question(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='examen',
    )
    text = models.CharField('enunciado', max_length=300)

    class Meta:
        verbose_name = 'pregunta'
        verbose_name_plural = 'preguntas'
        ordering = ['id']

    def __str__(self):
        return self.text


class Option(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='pregunta',
    )
    text = models.CharField('texto', max_length=200)
    is_correct = models.BooleanField('es correcta', default=False)

    class Meta:
        verbose_name = 'opción'
        verbose_name_plural = 'opciones'
        ordering = ['id']

    def __str__(self):
        return self.text
