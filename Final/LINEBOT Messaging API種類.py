"""
官方Messaging API reference
https://developers.line.biz/en/reference/messaging-api/#text-message
"""
# 文字訊息
text_message_payload = {
    "type": "text",
    "text": "這是文字訊息"
}

# 圖片訊息
image_message_payload = {
    "type": "image",
    "originalContentUrl": "https://example.com/original.jpg",
    "previewImageUrl": "https://example.com/preview.jpg"
}

# 影片訊息
video_message_payload = {
    "type": "video",
    "originalContentUrl": "https://example.com/original.mp4",
    "previewImageUrl": "https://example.com/preview.jpg"
}

# 語音訊息
audio_message_payload = {
    "type": "audio",
    "originalContentUrl": "https://example.com/audio.mp3",
    "duration": 60000
}

# 影像地圖訊息，baseUrl可於結尾加上#或?以正常顯示
imagemap_message_payload = {
    "type": "imagemap",
    "baseUrl": "https://example.com/base",
    "altText": "這是影像地圖訊息",
    "baseSize": {
        "width": 1040,
        "height": 1040
    },
    "actions": [
        {
            "type": "uri",
            "linkUri": "https://example.com",
            "area": {
                "x": 0,
                "y": 0,
                "width": 520,
                "height": 1040
            }
        }
    ]
}

# 貼圖訊息
sticker_message_payload = {
    "type": "sticker",
    "packageId": "446",
    "stickerId": "1988"
}

# 位置訊息
location_message_payload = {
    "type": "location",
    "title": "國立臺北商業大學",
    "address": "100台北市中正區濟南路一段321號",
    "latitude": 25.0423998,
    "longitude": 121.5228949
}

# 按鈕範本訊息
buttons_template_payload = {
    "type": "template",
    "altText": "這是按鈕範本訊息",
    "template": {
        "type": "buttons",
        "thumbnailImageUrl": "https://example.com/image.jpg",
        "title": "按鈕標題",
        "text": "按鈕內容",
        "actions": [
            {
                "type": "postback",
                "label": "按鈕1",
                "data": "action=buy&itemid=123"
            },
            {
                "type": "uri",
                "label": "按鈕2",
                "uri": "https://example.com"
            }
        ]
    }
}

# 輪播範本訊息
carousel_template_payload = {
    "type": "template",
    "altText": "這是輪播範本訊息",
    "template": {
        "type": "carousel",
        "columns": [
            {
                "thumbnailImageUrl": "https://example.com/image1.jpg",
                "title": "項目1",
                "text": "內容1",
                "actions": [
                    {
                        "type": "uri",
                        "label": "更多資訊",
                        "uri": "https://example.com/1"
                    }
                ]
            },
            {
                "thumbnailImageUrl": "https://example.com/image2.jpg",
                "title": "項目2",
                "text": "內容2",
                "actions": [
                    {
                        "type": "uri",
                        "label": "更多資訊",
                        "uri": "https://example.com/2"
                    }
                ]
            }
        ]
    }
}

# 確認範本訊息
confirm_template_payload = {
    "type": "template",
    "altText": "這是確認範本訊息",
    "template": {
        "type": "confirm",
        "text": "你確定要繼續嗎？",
        "actions": [
            {
                "type": "message",
                "label": "是",
                "text": "是"
            },
            {
                "type": "message",
                "label": "否",
                "text": "否"
            }
        ]
    }
}

# 圖片輪播範本訊息
image_carousel_payload = {
    "type": "template",
    "altText": "這是圖片輪播範本訊息",
    "template": {
        "type": "image_carousel",
        "columns": [
            {
                "imageUrl": "https://example.com/image1.jpg",
                "action": {
                    "type": "uri",
                    "label": "查看",
                    "uri": "https://example.com/1"
                }
            },
            {
                "imageUrl": "https://example.com/image2.jpg",
                "action": {
                    "type": "uri",
                    "label": "查看",
                    "uri": "https://example.com/2"
                }
            }
        ]
    }
}

# 互動原型型訊息
flex_message_payload = {
    "type": "flex",
    "altText": "這是互動原型型訊息",
    "contents": {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "這是 Flex Message",
                    "weight": "bold",
                    "size": "xl"
                }
            ]
        }
    }
}