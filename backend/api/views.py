import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import EquipmentData
from .serializers import EquipmentDataSerializer
from django.http import HttpResponse
from reportlab.pdfgen import canvas
import io
import json

class UploadView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_csv(file)

            def get_col(df, candidates):
                for col in df.columns:
                    if col.lower() in [c.lower() for c in candidates]:
                        return col
                return None

            flow_col = get_col(df, ['Flowrate', 'Flow Rate', 'Flow_Rate'])
            press_col = get_col(df, ['Pressure'])
            temp_col = get_col(df, ['Temperature', 'Temp'])
            
            total_count = len(df)
            avg_flow = df[flow_col].mean() if flow_col else 0
            avg_pressure = df[press_col].mean() if press_col else 0
            avg_temp = df[temp_col].mean() if temp_col else 0

            dist_col = get_col(df, ['Type', 'EquipmentType']) or get_col(df, ['Status'])
            
            equipment_distribution = (
                df[dist_col].value_counts().to_dict()
                if dist_col
                else {}
            )

            data_entry = EquipmentData.objects.create(
                filename=file.name,
                total_count=total_count,
                avg_flowrate=avg_flow,
                avg_pressure=avg_pressure,
                avg_temperature=avg_temp,
                equipment_distribution=equipment_distribution
            )

            ids_to_keep = EquipmentData.objects.order_by('-id').values_list('id', flat=True)[:5]
            EquipmentData.objects.exclude(id__in=ids_to_keep).delete()

            serializer = EquipmentDataSerializer(data_entry)

            preview_data = df.head(500).fillna(0).to_dict(orient='records')

            return Response({
                "summary": serializer.data,
                "data": preview_data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SummaryView(APIView):
    def get(self, request):
        latest = EquipmentData.objects.last()
        if not latest:
            return Response({})
        serializer = EquipmentDataSerializer(latest)
        return Response(serializer.data)

class HistoryView(APIView):
    def get(self, request):
        history = EquipmentData.objects.order_by('-id')[:5]
        serializer = EquipmentDataSerializer(history, many=True)
        return Response(serializer.data)

class LoginView(APIView):
    permission_classes = [] 

    def post(self, request):
        from django.contrib.auth import authenticate
        from rest_framework.authtoken.models import Token
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "user": username})
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class ReportView(APIView):
    def get(self, request):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 800, "Chemical Equipment Parameter Report")
        p.setFont("Helvetica", 10)
        
        local_now = timezone.localtime(timezone.now())
        p.drawString(100, 780, f"Generated: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        y = 750
        records = EquipmentData.objects.order_by('-id')[:5]
        
        if not records:
             p.drawString(100, y, "No data available.")
        
        for i, record in enumerate(records):
            if y < 200: 
                p.showPage()
                y = 800
                
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y, f"Dataset {i+1}: {record.filename}")
            y -= 20
            
            p.setFont("Helvetica", 10)
            local_upload = timezone.localtime(record.upload_date)
            p.drawString(120, y, f"Upload Date: {local_upload.strftime('%Y-%m-%d %H:%M')}")
            y -= 15
            p.drawString(120, y, f"Total Records: {record.total_count}")
            y -= 15
            p.drawString(120, y, f"Avg Flow Rate: {record.avg_flowrate:.2f}")
            y -= 15
            p.drawString(120, y, f"Avg Pressure: {record.avg_pressure:.2f}")
            y -= 15
            p.drawString(120, y, f"Avg Temperature: {record.avg_temperature:.2f}")
            y -= 15
            
            dist_str = ", ".join([f"{k}: {v}" for k, v in record.equipment_distribution.items()])
            p.drawString(120, y, f"Distribution: {dist_str}")
            
            y -= 40 

        p.showPage()
        p.save()
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')

class ClearHistoryView(APIView):
    def post(self, request):
        EquipmentData.objects.all().delete()
        return Response({"message": "History cleared"}, status=status.HTTP_200_OK)
