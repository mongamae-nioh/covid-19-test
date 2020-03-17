# coding: UTF-8
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_model import ui

import boto3
from boto3.dynamodb.conditions import Key, Attr
import json

import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 新型コロナの情報をDynamoDBへ保存している人向け
## DynamoDBテーブル名やクエリなど(テーブル名は環境に合わせて変えてください)
tablename = 'COVID-19_Hokkaido'
sb = StandardSkillBuilder(table_name=tablename)

## DynamoDBの設定(リージョンは環境に合わせて変えてください)
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table(tablename)
response = table.scan()

# 発話や画面表示内容
# 発話の間の調整
break_200ms = '<break time=\"200ms\"/>'
break_300ms = '<break time=\"300ms\"/>'
break_400ms = '<break time=\"400ms\"/>'
break_700ms = '<break time=\"700ms\"/>'

## DynamoDBのレスポンスを格納
contacts_subtotal = response['Items'][0]['contacts_subtotal'] # 新型コロナコールセンター相談件数(札幌市保健所値)(1日分)
discharges_subtotal = response['Items'][0]['discharges_subtotal'] # 治療終了者数(1日分)
discharges_total = response['Items'][0]['discharges_total'] # 治療終了者数(累計)
inspections_subtotal = response['Items'][0]['inspections_subtotal'] # 検査数累計(1日分)
inspections_total = response['Items'][0]['inspections_total'] # 検査数累計(累計)
latest_patients_subtotal = response['Items'][0]['latest_patients_subtotal'] # 現在の患者数(治療終了者反映)(1日分)
latest_patients_total = response['Items'][0]['latest_patients_total'] # 現在の患者数(治療終了者反映)(合計)
patients_subtotal = response['Items'][0]['patients_subtotal'] # 陽性患者数(1日分)
patients_total = response['Items'][0]['patients_total'] # 陽性患者数(累計)
patients_residential = response['Items'][0]['patients_residential'] # 陽性患者の居住地(リスト)
parients_attribute = f'{break_200ms}'.join(patients_residential) # 陽性患者の居住地リストをAlexaが間をとって話すため
querents_subtotal = response['Items'][0]['querents_subtotal'] # 帰国者・接触者電話相談センター相談件数(札幌市保健所値)(1日分)
update_date = response['Items'][0]['update_date'] # データ更新日
year = update_date[:4]
month = update_date[5:7]
day = update_date[8:10]
update_time = response['Items'][0]['update_time'] # データ更新時間

## 報告人数により発話内容変更
if patients_subtotal <= 0:
    patients_subtotal_text = '<p>陽性と診断されたかたの報告はありません。'
else:
    patients_subtotal_text = f'<p>新たに{patients_subtotal}人のかたが陽性と診断されました。{break_300ms}居住地は、{parients_attribute}です。'

if discharges_subtotal <= 0:
    discharges_subtotal_text = f'陰性と診断されたかたの報告はありません。{break_300ms}'
else:
    discharges_subtotal_text = f'一方、陰性と診断されたかたは、新たに{discharges_subtotal}人{break_300ms}'

## 患者数など(都府県の情報に合わせて変えてください)
SPEECH_TITLE = f'{year}年{month}月{day}日、{update_time}現在の北海道の新型コロナウイルスの情報です。'

SPEECH_BODY = f'{break_700ms}{patients_subtotal_text}' \
              f'{break_300ms}これまでの累計患者数は、{patients_total}人です。' \
              f'{break_300ms}なお、現在の患者数は、{latest_patients_total}人です。' \
              f'{break_700ms}{discharges_subtotal_text}治療が終了したかたは延べ{discharges_total}人です。' \
              f'{break_700ms}これまでに検査を受けたかたは合計で{inspections_total}人にのぼります。</p>'

## 相談窓口(都府県の情報に合わせて変えてください)
## <say-as interpret-as="telephone">nnn-nnn-nnnn</say-as>を使うとAlexaが電話番号のように読んでくれます
## 詳しくはSSML(https://developer.amazon.com/ja-JP/docs/alexa/custom-skills/speech-synthesis-markup-language-ssml-reference.html)を参照
INQUIRY_TEXT = '<speak><p>新型コロナウイルスの相談窓口をお伝えします。' \
               f'{break_300ms}風邪の症状や、37.5度以上の発熱が4日以上続いている、' \
               f'{break_300ms}強いだるさ、倦怠感や息苦しさ、呼吸困難がある。' \
               f'{break_300ms}高齢者や基礎疾患などのあるかたで、この状態が二日程度続いている場合。' \
               f'{break_300ms}これらの症状のかたは、最寄りの、帰国者、接触者相談センターへご相談ください。{break_700ms}それでは、窓口と電話番号をお伝えします。' \
               f'{break_700ms}札幌市保健所、<say-as interpret-as="telephone">011-272-7119</say-as>{break_400ms}<say-as interpret-as="telephone">011-272-7119</say-as>{break_400ms}開設時間は24時間。' \
               f'{break_300ms}旭川市保健所、<say-as interpret-as="telephone">0166-25-9848</say-as>{break_400ms}<say-as interpret-as="telephone">0166-25-9848</say-as>{break_400ms}土日祝日を含む、8時45分から21時まで。' \
               f'{break_300ms}市立函館保健所、<say-as interpret-as="telephone">0138-32-1547</say-as>{break_400ms}<say-as interpret-as="telephone">0138-32-1547</say-as>{break_400ms}平日、8時45分から19時まで。' \
               f'{break_300ms}小樽市保健所、<say-as interpret-as="telephone">0134-22-3110</say-as>{break_400ms}<say-as interpret-as="telephone">0134-22-3110</say-as>{break_400ms}平日、8時45分から17時20分までです。' \
               f'{break_300ms}これらの地域以外にお住まいのかたは、北海道保険福祉部、健康安全局地域保健課、<say-as interpret-as="telephone">011-204-5020</say-as>{break_400ms}<say-as interpret-as="telephone">011-204-5020</say-as>へご相談ください。開設時間は24時間です。' \
               f'{break_700ms}つぎに、ご自身の症状に不安がある場合など、一般的なお問い合わせについては、次の最寄りの窓口へご相談ください。' \
               f'{break_300ms}厚生労働省、電話相談窓口、フリーダイヤル、<say-as interpret-as="telephone">0120-565-653</say-as>{break_400ms}<say-as interpret-as="telephone">0120-565-653</say-as>{break_400ms}土日祝日を含む、9時から21時まで。' \
               f'{break_300ms}札幌市保健所、新型コロナウイルス一般電話相談窓口、<say-as interpret-as="telephone">011-632-4567</say-as>{break_400ms}<say-as interpret-as="telephone">011-632-4567</say-as>{break_400ms}土日祝日を含む、9時から21時まで。' \
               f'{break_300ms}旭川市保健所、<say-as interpret-as="telephone">0166-26-2397</say-as>{break_400ms}<say-as interpret-as="telephone">0166-26-2397</say-as>{break_400ms}平日、8時45分から17時15分まで。' \
               f'{break_300ms}市立函館保健所、<say-as interpret-as="telephone">0138-32-1547</say-as>{break_400ms}<say-as interpret-as="telephone">0138-32-1547</say-as>{break_400ms}平日、8時45分から17時30分まで。' \
               f'{break_300ms}小樽市保健所、<say-as interpret-as="telephone">0134-22-3110</say-as>{break_400ms}<say-as interpret-as="telephone">0134-22-3110</say-as>{break_400ms}平日、8時45分から17時20分までです。' \
               f'{break_300ms}これらの地域以外にお住まいのかたは、北海道保険福祉部、健康安全局地域保健課、<say-as interpret-as="telephone">011-204-5020</say-as>{break_400ms}<say-as interpret-as="telephone">011-204-5020</say-as>へご相談ください。開設時間は24時間です。</p></speak>' \

## 前日比用
if latest_patients_subtotal < 0:
    plus_or_minus = ''
else:
    plus_or_minus = '＋'

## 画面表示情報(画面付きデバイスのみ)(都府県の情報に合わせて変えてください)
LAUNCH_CARD_TITLE = f'北海道の新型コロナウイルス状況({year}年{month}月{day}日{update_time}現在)'
LAUNCH_CARD_BODY = f'陽性患者数累計:{patients_total}人 (前日比＋{patients_subtotal}）\n' \
                   f'現在の患者数:{latest_patients_total}人 (前日比{plus_or_minus}{latest_patients_subtotal}）\n' \
                   f'治療終了者数:{discharges_total}人 (前日比＋{discharges_subtotal}) \n' \
                   f'新型コロナコールセンター相談件数(札幌市保健所値):{contacts_subtotal}件 \n' \
                   f'帰国者・接触者電話相談センター相談件数(札幌市保健所値):{querents_subtotal}件 \n' \

INQUIRY_CARD_TITLE = '北海道の新型コロナウイルス相談窓口'
INQUIRY_CARD_BODY = '症状がある方向けの窓口と一般的なお問い合わせの窓口は違うのでご注意ください。'

## ヘルプインテント用発話(都府県の情報に合わせて変えてください)
HELP_SPEECH_BODY = '北海道の新型コロナウイルスの情報をお伝えします。患者の数や、治療が終了したかたの数を知ることができます。' \
                   'また、相談窓口の連絡先や開設時間を知りたい場合は、アレクサ、北海道新型コロナ情報で相談窓口を教えて、と言ってください。'

# Alexaスキル(発話内容や画面表示は上の変数で適宜変えてください)
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):
        speech_title = SPEECH_TITLE
        speech_body = SPEECH_BODY

        handler_input.response_builder.speak(speech_title+speech_body).set_card(
            ui.SimpleCard(
                LAUNCH_CARD_TITLE,
                LAUNCH_CARD_BODY
                )
            )
        return handler_input.response_builder.response  

class InquiryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("InquiryIntent")(handler_input)

    def handle(self, handler_input):
        speech_text = INQUIRY_TEXT
        
        handler_input.response_builder.speak(speech_text).set_card(
            ui.SimpleCard(
                INQUIRY_CARD_TITLE,
                INQUIRY_CARD_BODY
                )
            )
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    
    def handle(self, handler_input):
        speech_text = HELP_SPEECH_BODY
        
        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response  
        
class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In CancelOrStopIntentHandler")

        speech_text = 'わかりました。'

        handler_input.response_builder.speak(speech_text)
        return handler_input.response_builder.response

class AllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):

        # Log the exception in CloudWatch Logs
        print(exception)

        speech = "すみません、わかりませんでした。もう一度言ってください。"
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(InquiryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(AllExceptionHandler())

handler = sb.lambda_handler()