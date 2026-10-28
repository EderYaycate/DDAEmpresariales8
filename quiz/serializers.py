from django.db import transaction
from rest_framework import serializers

from .models import Exam, Option, Question


class ExamSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ['id', 'title', 'description', 'created_at', 'question_count']
        read_only_fields = ['id', 'created_at']

    def get_question_count(self, obj):
        # The viewset annotates the count (no extra query per exam); a freshly
        # created exam has no annotation, so fall back to counting.
        annotated = getattr(obj, 'question_count', None)
        return annotated if annotated is not None else obj.questions.count()


class NestedOptionSerializer(serializers.ModelSerializer):
    """Option as it travels inside a question: no question id, it is implicit."""

    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']
        read_only_fields = ['id']


class QuestionSerializer(serializers.ModelSerializer):
    # Relations: the options travel NESTED inside the question (they only make
    # sense together), while the exam is referred to by its ID.
    options = NestedOptionSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'exam', 'text', 'options']
        read_only_fields = ['id']

    def validate_options(self, options):
        correct = sum(1 for option in options if option.get('is_correct', False))
        if correct != 1:
            raise serializers.ValidationError(
                f'La pregunta debe tener exactamente una opción correcta (recibidas: {correct}).'
            )
        return options

    @transaction.atomic
    def create(self, validated_data):
        options = validated_data.pop('options')
        question = Question.objects.create(**validated_data)
        Option.objects.bulk_create(Option(question=question, **item) for item in options)
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        options = validated_data.pop('options', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # When "options" is sent, it replaces the whole set; when it is absent
        # (a partial update), the existing options stay untouched.
        if options is not None:
            instance.options.all().delete()
            Option.objects.bulk_create(Option(question=instance, **item) for item in options)
        return instance


class OptionSerializer(serializers.ModelSerializer):
    """Option as a standalone resource: here the question is referred to by ID."""

    class Meta:
        model = Option
        fields = ['id', 'question', 'text', 'is_correct']
        read_only_fields = ['id']

    def validate(self, attrs):
        # Keep the "exactly one correct option" rule when options are edited one by one.
        question = attrs.get('question', getattr(self.instance, 'question', None))
        is_correct = attrs.get('is_correct', getattr(self.instance, 'is_correct', False))
        if question is None:
            return attrs
        others = Option.objects.filter(question=question, is_correct=True)
        if self.instance is not None:
            others = others.exclude(pk=self.instance.pk)
        if is_correct and others.exists():
            raise serializers.ValidationError(
                'La pregunta ya tiene una opción correcta. Para cambiarla, '
                'modifica la pregunta enviando todas sus opciones.'
            )
        if not is_correct and not others.exists():
            raise serializers.ValidationError(
                'La pregunta se quedaría sin opción correcta.'
            )
        return attrs
