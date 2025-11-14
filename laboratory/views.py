from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from laboratory.models import Analysis
from laboratory.serializers import AnalysisSerializer
from user.views import PartialPutMixin
from rest_framework.response import Response


@extend_schema(tags=['Analysis'])
class AnalysisViewSet(viewsets.ModelViewSet, PartialPutMixin):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()

        dailyanalysiscount = Analysis.objects.filter(created_at__date=today).count()
        totalanalysiscount = Analysis.objects.all().count()
        newanalysiscount = Analysis.objects.filter(status=Analysis.Status.new, created_at__date=today).count()
        inprogressalaysiscount = Analysis.objects.filter(status=Analysis.Status.in_progress,
                                                         created_at__date=today).count()
        lastanalysis = Analysis.objects.filter(created_at__date=today).order_by('-created_at').first()
        finishedanalysiscount = Analysis.objects.filter(status=Analysis.Status.finished, created_at__date=today).count()

        data = {
            'kunlik_tahlil': dailyanalysiscount,
            'jami_tahlil': totalanalysiscount,
            'yangi_tahlil': newanalysiscount,
            'jarayondagi_tahlil': inprogressalaysiscount,
            'yakunlangan_tahlil': finishedanalysiscount,
            'oxirgi_tshlillar': (AnalysisSerializer(lastanalysis, context={'request': request}).data if
                                 lastanalysis else None)
        }

        return Response(data, status=status.HTTP_200_OK)
