from rest_framework.routers import DefaultRouter

from .views import ExamViewSet, OptionViewSet, QuestionViewSet

router = DefaultRouter()
router.register('exams', ExamViewSet)
router.register('questions', QuestionViewSet)
router.register('options', OptionViewSet)

urlpatterns = router.urls
