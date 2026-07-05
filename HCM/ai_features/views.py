from collections import defaultdict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from dotenv import load_dotenv
import os

from supabase import create_client, Client
from google import genai
import os
from datetime import date
import json

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)


class StockPredictionAPIView(APIView):
    def get(self, request):
        stock_response = (
            supabase.table("medicine_stock")
            .select(
                "id,centre_id,district_id,quantity,last_updated,medicine_id,medicine:medicine_id(id,name,unit,minimum_stock)"
            )
            .execute()
        )

        history_response = (
            supabase.table("medicine_stock_history")
            .select("medicine_id,quantity")
            .order("recorded_at")
            .execute()
        )

        history_map = defaultdict(list)

        for row in history_response.data:
            history_map[row["medicine_id"]].append(row["quantity"])

        predictions = []

        for item in stock_response.data:
            medicine = item["medicine"]
            quantity = item["quantity"]
            minimum_stock = medicine["minimum_stock"]

            history = history_map.get(item["medicine_id"], [])

            usage = []

            if len(history) > 1:
                for i in range(len(history) - 1):
                    diff = history[i] - history[i + 1]
                    if diff > 0:
                        usage.append(diff)

            avg_daily_usage = (
                round(sum(usage) / len(usage), 2)
                if usage else 1
            )

            estimated_days = max(
                1,
                round(quantity / avg_daily_usage)
            )

            if quantity <= minimum_stock:
                risk = "High"
                stock_status = "Critical"
                recommendation = (
                    f"Immediate replenishment of {medicine['name']} is required."
                )

            elif quantity <= minimum_stock * 2:
                risk = "Medium"
                stock_status = "Low"
                recommendation = (
                    f"Restock {medicine['name']} within the next few days."
                )

            else:
                continue

            predictions.append(
                {
                    "centre_id": item["centre_id"],
                    "district_id": item["district_id"],
                    "medicine": medicine["name"],
                    "available_quantity": quantity,
                    "minimum_stock": minimum_stock,
                    "average_daily_usage": avg_daily_usage,
                    "estimated_days_left": estimated_days,
                    "stock_status": stock_status,
                    "risk_level": risk,
                    "recommendation": recommendation,
                    "last_updated": item["last_updated"],
                }
            )

        predictions.sort(key=lambda x: x["estimated_days_left"])

        return Response(predictions, status=status.HTTP_200_OK)

# views.py


class PatientFootfallAnalysisView(APIView):

    def get(self, request):
        try:
            # Fetch patient footfall data
            response = (
                supabase.table("patient_footfall")
                .select(
                    "entry_date, opd_count, ipd_count, total_patients, centre_id, district_id"
                )
                .order("entry_date", desc=False)
                .execute()
            )

            data = response.data

            if not data:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No patient footfall data found."
                    },
                    status=404,
                )

            # Gemini Client
            client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )

            prompt = f"""
You are an AI healthcare analytics assistant.

Analyze the following patient footfall data collected from PHCs/CHCs.

Data:
{data}

Generate response strictly in JSON format:

{{
    "summary": "",
    "overall_patient_trend": "",
    "peak_day": "",
    "highest_patient_count": 0,
    "lowest_patient_count": 0,
    "average_daily_patients": 0,
    "forecast_next_day": 0,
    "risk_level": "",
    "recommendations": [
        "",
        "",
        ""
    ]
}}

Do not include markdown.
Do not explain anything outside JSON.
"""

            result = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            

            analysis = result.text.strip()

            # Remove markdown if Gemini returns ```json ... ```
            if analysis.startswith("```"):
                analysis = analysis.replace("```json", "").replace("```", "").strip()

            analysis = json.loads(analysis)

            return JsonResponse(
                {
                    "success": True,
                    "analysis": analysis,
                }
            )

        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": str(e),
                },
                status=500,
            )
        



class ResourceRedistributionView(APIView):

    def get(self, request):
        try:

            # Fetch medicine stock with centre details
            response = (
                supabase.table("medicine_stock")
                .select("""
                    quantity,
                    medicine:medicine_id(id,name,minimum_stock),
                    centre:centre_id(id,name)
                """)
                .execute()
            )

            stock_data = response.data

            if not stock_data:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No medicine stock data found."
                    },
                    status=404,
                )

            # Gemini Client
            client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )

            prompt = f"""
You are an AI Healthcare Resource Optimization Assistant.

Analyze the following medicine stock data from multiple PHCs/CHCs.

Data:
{stock_data}

Identify:
1. Centres having surplus medicine.
2. Centres having shortage.
3. Recommend redistribution between nearby centres (ignore actual distance for prototype).
4. Explain why redistribution is required.
5. Assign priority (High, Medium, Low).

Return ONLY valid JSON.

{{
    "summary": "",
    "redistributions": [
        {{
            "medicine": "",
            "from_centre": "",
            "to_centre": "",
            "available_stock": 0,
            "required_stock": 0,
            "recommended_transfer": 0,
            "priority": "",
            "reason": ""
        }}
    ],
    "overall_status": "",
    "general_recommendations": [
        "",
        "",
        ""
    ]
}}
"""

            result = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            analysis = result.text.strip()

            if analysis.startswith("```"):
                analysis = (
                    analysis.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

            analysis = json.loads(analysis)

            return JsonResponse(
                {
                    "success": True,
                    "analysis": analysis
                }
            )

        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "error": str(e)
                },
                status=500
            )