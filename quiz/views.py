from django.db.models import Count
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter

from .models import Exam, Option, Question
from .serializers import ExamSerializer, OptionSerializer, QuestionSerializer


def filter_by_id_param(queryset, request, param, field):
    """Filter a list by an integer query parameter (e.g. ?exam=1)."""
    value = request.query_params.get(param)
    if value is None:
        return queryset
    if not value.isdigit():
        raise ValidationError({param: 'Debe ser un número entero.'})
    return queryset.filter(**{field: int(value)})


class ExamViewSet(viewsets.ModelViewSet):
    # annotate() with an aggregate drops Meta.ordering, so order explicitly for stable pages
    queryset = Exam.objects.annotate(question_count=Count('questions')).order_by('id')
    serializer_class = ExamSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title']


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.prefetch_related('options')
    serializer_class = QuestionSerializer
    filter_backends = [SearchFilter]
    search_fields = ['text']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = filter_by_id_param(queryset, self.request, 'exam', 'exam_id')
        return queryset


class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    filter_backends = [SearchFilter]
    search_fields = ['text']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = filter_by_id_param(queryset, self.request, 'question', 'question_id')
        return queryset

    def perform_destroy(self, instance):
        if instance.is_correct:
            raise ValidationError(
                {'detail': 'No se puede eliminar la opción correcta de una pregunta.'}
            )
        instance.delete()
