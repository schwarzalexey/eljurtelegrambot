from PIL import Image, ImageDraw, ImageFont


def draw(data, user_id):
    max_len_lesson = max([len(f"{x}. {y['name']}") * 7 for x, y in data['lessons'].items()])
    max_len_hw = max([len(data['lessons'][str(i)]['hometask'] if data['lessons'][str(i)]['hometask'] is not None else '') * 7 for i in range(1, (len(data['lessons'])+1))])
    max_len = max_len_hw + max_len_lesson + 120
    image = Image.new("RGB", (max_len, 50*(len(data['lessons'])+1)), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    semibold_font = ImageFont.truetype('Inter-SemiBold.ttf', 18)
    regular_font = ImageFont.truetype('Inter-Regular.ttf', 14)
    draw.text((10, 14), f"{data['day']}, {data['date']}", fill=(0,0,0), font=semibold_font)
    ht_logo = Image.open('ht.png').convert("RGBA").resize((20, 20))
    for x, y in data['lessons'].items():
        x = x if x != '' else '-1'
        if int(x) % 2:
            draw.rectangle([(0, 50*int(x)), (max_len, 50*int(x) + 50)], fill=(230, 230, 230), outline=(230, 230, 230))
        draw.text((10, 16 + 50*int(x)), f"{x}. {y['name']}", fill=(0, 0, 0), font=regular_font)
        image.paste(ht_logo, (max_len_lesson+25, 15+50*int(x)), ht_logo)
        if y['hometask'] is None:
            y['hometask'] = 'Нет'
        draw.text((max_len_lesson+50, 16 + 50 * int(x)), y['hometask'], fill=(0, 0, 0), font=regular_font)
        if y['mark'] is not None:
            mark = y['mark'] if y['mark'] != '' else 'Н'
            draw.rounded_rectangle([(max_len_lesson+max_len_hw+75, 10 + 50*int(x)), (max_len_lesson+max_len_hw+105, 40 + 50*int(x))], radius=10, outline=(150,150,150), width=1)
            draw.text((max_len_lesson+max_len_hw+85, 16 + 50*int(x)), mark, fill=(0, 0, 0), font=regular_font)
    image.save(f'day_{user_id}.jpg', quality=95)




