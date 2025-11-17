from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from laboratory.models import Analysis, Result
from laboratory.serializers import AnalysisSerializer, AnalysisPostSerializer, AnalysisSearchInputSerializer, \
    ResultSerializer
from user.views import PartialPutMixin
from rest_framework.response import Response
from django.db.models import Q
from rest_framework import generics


@extend_schema(tags=['Analysis'])
class AnalysisViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AnalysisPostSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()

        dailyanalysiscount = Analysis.objects.filter(created_at__date=today).count()
        totalanalysiscount = Analysis.objects.all().count()
        newanalysiscount = Analysis.objects.filter(status=Analysis.Status.new, created_at__date=today).count()
        inprogressalaysiscount = Analysis.objects.filter(status=Analysis.Status.in_progress,
                                                         created_at__date=today).count()
        lastanalysis = Analysis.objects.all().order_by('-created_at')[:10]
        finishedanalysiscount = Analysis.objects.filter(status=Analysis.Status.finished, created_at__date=today).count()

        data = {
            'kunlik_tahlil': dailyanalysiscount,
            'jami_tahlil': totalanalysiscount,
            'yangi_tahlil': newanalysiscount,
            'jarayondagi_tahlil': inprogressalaysiscount,
            'yakunlangan_tahlil': finishedanalysiscount,
            'oxirgi_tahlillar': (AnalysisSerializer(lastanalysis, many=True, context={'request': request}).data if
                                 lastanalysis else None)
        }

        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(methods=['POST'], request=AnalysisSearchInputSerializer,
                   responses={200: AnalysisSerializer(many=True)}, )
    @action(detail=False, methods=['post'])
    def search(self, request):
        serializer = AnalysisSearchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        search_value = serializer.validated_data['search']

        queryset = Analysis.objects.filter(
            Q(analysis_result__icontains=search_value)
            | Q(analysis_result_uz__icontains=search_value)
            | Q(analysis_result_ru__icontains=search_value)
            | Q(status__icontains=search_value)
            | Q(patient__name__icontains=search_value)
            | Q(patient__last_name__icontains=search_value)
            | Q(patient__middle_name__icontains=search_value)
            | Q(patient__phone_number__icontains=search_value)
            | Q(department_types__title__icontains=search_value)
        ).distinct()

        output = AnalysisSerializer(queryset, many=True, context={'request': request})
        return Response(output.data)


@extend_schema(tags=['Result'])
class ResultViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']


@extend_schema(tags=['Result'])
class ResultByDepartmentDetailAPIView(generics.ListAPIView):
    serializer_class = ResultSerializer

    def get_queryset(self):
        department_type_id = self.kwargs.get('department_type_id')
        return Result.objects.filter(analysis__department_types_id=department_type_id)
