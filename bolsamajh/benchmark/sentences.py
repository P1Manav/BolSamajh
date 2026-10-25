"""100 Hinglish benchmark sentences categorized for speech-to-text evaluation.

Categories:
1. Everyday conversation (30)
2. Technical / Programming / Work (20)
3. Numbers, Currency, Dates & Phone numbers (20)
4. Indian names, Brands & Places (15)
5. Mid-sentence Code-switching (15)
"""

from dataclasses import dataclass
from typing import List


@dataclass
class BenchmarkSentence:
    id: int
    category: str
    reference_roman: str
    reference_devanagari: str
    notes: str = ""


SENTENCES: List[BenchmarkSentence] = [
    # ── Category 1: Everyday conversation (30) ──
    BenchmarkSentence(1, "everyday", "Yaar kal meeting kitne baje schedule ki hai?", "यार कल मीटिंग कितने बजे शेड्यूल की है?", "Informal scheduling"),
    BenchmarkSentence(2, "everyday", "Main thodi der me call back karta hoon, abhi drive kar raha hoon.", "मैं थोड़ी देर में कॉल बैक करता हूँ, अभी ड्राइव कर रहा हूँ।", "Status update"),
    BenchmarkSentence(3, "everyday", "Chai peene chalte hain, bohot tired feel ho raha hai.", "चाय पीने चलते हैं, बहुत टायर्ड फील हो रहा है।", "Casual break"),
    BenchmarkSentence(4, "everyday", "Tumne lunch order kiya kya ya bahar chalna hai?", "तुमने लंच ऑर्डर किया क्या या बाहर चलना है?", "Food order"),
    BenchmarkSentence(5, "everyday", "Mera laptop restart ho gaya aur saara unsaved kaam chala gaya.", "मेरा लैपटॉप रीस्टार्ट हो गया और सारा अनसेव्ड काम चला गया।", "Tech annoyance"),
    BenchmarkSentence(6, "everyday", "Traffic bohot zyada tha isliye reach karne me late ho gaya.", "ट्रैफिक बहुत ज़्यादा था इसलिए रीच करने में लेट हो गया।", "Commute excuse"),
    BenchmarkSentence(7, "everyday", "Kya tum mujhe woh presentation forward kar sakte ho please?", "क्या तुम मुझे वो प्रेजेंटेशन फॉरवर्ड कर सकते हो प्लीज?", "Polite request"),
    BenchmarkSentence(8, "everyday", "Weekend pe kya plans hain tumhare?", "वीकेंड पे क्या प्लान्स हैं तुम्हारे?", "Social conversation"),
    BenchmarkSentence(9, "everyday", "Room ka AC theek se cooling nahi kar raha hai.", "रूम का एसी ठीक से कूलिंग नहीं कर रहा है।", "Household query"),
    BenchmarkSentence(10, "everyday", "Main shaam ko gym jaaunga, aaj leg day hai.", "मैं शाम को जिम जाऊंगा, आज लेग डे है।", "Fitness routine"),
    BenchmarkSentence(11, "everyday", "Wifi connect nahi ho raha hai, router restart karke dekho.", "वाईफाई कनेक्ट नहीं हो रहा है, राउटर रीस्टार्ट करके देखो।", "Troubleshooting"),
    BenchmarkSentence(12, "everyday", "Mera phone charge pe laga do agar switch board khali ho.", "मेरा फोन चार्ज पे लगा दो अगर स्विच बोर्ड खाली हो।", "Everyday request"),
    BenchmarkSentence(13, "everyday", "Weather bohot accha hai aaj, thandi hawa chal rahi hai.", "वेदर बहुत अच्छा है आज, ठंडी हवा चल रही है।", "Weather talk"),
    BenchmarkSentence(14, "everyday", "Mujhe lagta hai hume ek baar client se double check kar lena chahiye.", "मुझे लगता है हमें एक बार क्लाइंट से डबल चेक कर लेना चाहिए।", "Work caution"),
    BenchmarkSentence(15, "everyday", "Yeh wala movie trailer bohot exciting lag raha hai.", "यह वाला मूवी ट्रेलर बहुत एक्साइटिंग लग रहा है।", "Entertainment"),
    BenchmarkSentence(16, "everyday", "Subah se migraine ho raha hai, screen time kam karna padega.", "सुबह से माइग्रेन हो रहा है, स्क्रीन टाइम कम करना पड़ेगा।", "Health complaint"),
    BenchmarkSentence(17, "everyday", "Grocery shopping list me doodh aur eggs add kar do.", "ग्रॉसरी शॉपिंग लिस्ट में दूध और एग्स ऐड कर दो।", "Shopping list"),
    BenchmarkSentence(18, "everyday", "Flight delayed hai lagbhag do ghante ke liye.", "फ्लाइट डिलेड है लगभग दो घंटे के लिए।", "Travel update"),
    BenchmarkSentence(19, "everyday", "Tumhara new flat kaisa hai, shifted comfortable ho gaye?", "तुम्हारा न्यू फ्लैट कैसा है, शिफ्टेड कम्फर्टेबल हो गए?", "Settling in"),
    BenchmarkSentence(20, "everyday", "Main WhatsApp pe location share kar raha hoon, follow kar lena.", "मैं व्हाट्सएप पे लोकेशन शेयर कर रहा हूँ, फॉलो कर लेना।", "Directions"),
    BenchmarkSentence(21, "everyday", "Coffee bohot strong banayi hai tumne aaj.", "कॉफी बहुत स्ट्रॉन्ग बनाई है तुमने आज।", "Drink feedback"),
    BenchmarkSentence(22, "everyday", "Kal subah early morning walk pe chalte hain park me.", "कल सुबह अर्ली मॉर्निंग वॉक पे चलते हैं पार्क में।", "Morning plan"),
    BenchmarkSentence(23, "everyday", "Please door lock kar dena jab bahar niklo.", "प्लीज डोर लॉक कर देना जब बाहर निकलो।", "House reminder"),
    BenchmarkSentence(24, "everyday", "Mera parcel deliver ho gaya security desk par.", "मेरा पार्सल डिलीवर हो गया सिक्योरिटी डेस्क पर।", "Delivery alert"),
    BenchmarkSentence(25, "everyday", "Yeh dress bohot stylish lag rahi hai wedding ke liye.", "यह ड्रेस बहुत स्टाइलिश लग रही है वेडिंग के लिए।", "Fashion comment"),
    BenchmarkSentence(26, "everyday", "Online sale chal rahi hai Amazon par bohot acche discounts hain.", "ऑनलाइन सेल चल रही है अमेज़न पर बहुत अच्छे डिस्काउंट्स हैं।", "Shopping alert"),
    BenchmarkSentence(27, "everyday", "Battery low ho gayi hai, charger kahan rakha hai?", "बैटरी लो हो गई है, चार्जर कहाँ रखा है?", "Low battery"),
    BenchmarkSentence(28, "everyday", "Music volume thoda kam kar do please, focus nahi ho raha.", "म्यूजिक वॉल्यूम थोड़ा कम कर दो प्लीज, फोकस नहीं हो रहा।", "Noise control"),
    BenchmarkSentence(29, "everyday", "Main kal aapse office me personally discuss karunga yeh matter.", "मैं कल आपसे ऑफिस में पर्सनली डिस्कस करूंगा यह मैटर।", "Professional plan"),
    BenchmarkSentence(30, "everyday", "Bas pass me hi hoon, five minutes me pahunch raha hoon.", "बस पास में ही हूँ, फाइव मिनट्स में पहुँच रहा हूँ।", "ETA update"),

    # ── Category 2: Technical / Programming / Work (20) ──
    BenchmarkSentence(31, "technical", "Python me async function define karne ke liye async def use karo.", "पायथन में असिंक्रोनस फंक्शन डिफाइन करने के लिए असिंक डेफ़ यूज़ करो।", "Python syntax"),
    BenchmarkSentence(32, "technical", "Git merge conflict resolve karke branch ko rebase kar lo.", "गिट मर्ज कन्फ्लिक्ट रिज़ॉल्व करके ब्रांच को रीबेस कर लो।", "Git workflow"),
    BenchmarkSentence(33, "technical", "Docker container build karke AWS ECS pe deploy karna hai.", "डॉकर कंटेनर बिल्ड करके एडब्ल्यूएस ईसीएस पे डिप्लॉय करना है।", "DevOps pipeline"),
    BenchmarkSentence(34, "technical", "Database queries ko optimize karne ke liye proper indexing lagao.", "डेटाबेस क्वेरीज़ को ऑप्टिमाइज़ करने के लिए प्रॉपर इंडेक्सिंग लगाओ।", "DB optimization"),
    BenchmarkSentence(35, "technical", "FastAPI backend WebSocket connection handle kar raha hai.", "फास्टएपीआई बैकएंड वेबसॉकेट कनेक्शन हैंडल कर रहा है।", "FastAPI architecture"),
    BenchmarkSentence(36, "technical", "React state update directly mutate mat karo, setter function use karo.", "रिएक्ट स्टेट अपडेट डायरेक्टली म्यूटेट मत करो, सेटर फंक्शन यूज़ करो।", "React best practice"),
    BenchmarkSentence(37, "technical", "PyTorch model inference RTX 3060 Ti GPU par 40ms me run hota hai.", "पायटॉर्च मॉडल इन्फरेंस आरटीएक्स 3060 टीआई जीपीयू पर 40 मिलीसेकंड में रन होता है।", "GPU performance"),
    BenchmarkSentence(38, "technical", "REST API endpoint me rate limiting aur JWT authentication implement karo.", "रेस्ट एपीआई एंडपॉइंट में रेट लिमिटिंग और जेडब्ल्यूटी ऑथेंटिकेशन इम्प्लीमेंट करो।", "API security"),
    BenchmarkSentence(39, "technical", "FAISS vector store me cosine similarity search fast perform karti hai.", "फैस वेक्टर स्टोर में कोसाइन सिमिलैरिटी सर्च फास्ट परफॉर्म करती है।", "Vector search"),
    BenchmarkSentence(40, "technical", "Microservices communication ke liye gRPC ya RabbitMQ select kar sakte hain.", "माइक्रोसर्विस कम्युनिकेशन के लिए जीआरपीसी या रैबिटएमक्यू सेलेक्ट कर सकते हैं।", "Distributed systems"),
    BenchmarkSentence(41, "technical", "Pull request review karte waqt unit test coverage verify kar lena.", "पुल रिक्वेस्ट रिव्यू करते वक्त यूनिट टेस्ट कवरेज वेरीफाई कर लेना।", "Code review"),
    BenchmarkSentence(42, "technical", "Frontend styling Tailwind CSS ya pure CSS modules me maintain karo.", "फ्रंटएंड स्टाइलिंग टेलविंड सीएसएस या प्योर सीएसएस मॉड्यूल्स में मेंटेन करो।", "Frontend tooling"),
    BenchmarkSentence(43, "technical", "Memory leak identify karne ke liye heap profiler attach karo.", "मेमोरी लीक आइडेंटिफाई करने के लिए हीप प्रोफाइलर अटैच करो।", "Profiling"),
    BenchmarkSentence(44, "technical", "CI CD pipeline test cases fail hone par build reject kar deti hai.", "सीआई सीडी पाइपलाइन टेस्ट केसेस फेल होने पर बिल्ड रिजेक्ट कर देती है।", "CI/CD"),
    BenchmarkSentence(45, "technical", "Redis cache layer configure karo taaki database latency drop ho sake.", "रेडिस कैश लेयर कॉन्फ़िगर करो ताकि डेटाबेस लेटेंसी ड्रॉप हो सके।", "Caching"),
    BenchmarkSentence(46, "technical", "Open source Whisper model Hindi audio transcription accurately process karta hai.", "ओपन सोर्स व्हिस्पर मॉडल हिंदी ऑडियो ट्रांसक्रिप्शन एक्युरेटली प्रोसेस करता है।", "Voice AI"),
    BenchmarkSentence(47, "technical", "Kubernetes cluster me pod autoscaling metrics based set ki hai.", "कुबेरनेट्स क्लस्टर में पॉड ऑटोस्केलिंग मीट्रिक्स बेस्ड सेट की है।", "K8s"),
    BenchmarkSentence(48, "technical", "Edge computing architecture latency sensitive applications ke liye optimal hai.", "एज कंप्यूटिंग आर्किटेक्चर लेटेंसी सेंसिटिव एप्लिकेशन्स के लिए ऑप्टिमल है।", "System design"),
    BenchmarkSentence(49, "technical", "SQL query explain analyze karke execution plan verify kiya gaya.", "एसक्यूएल क्वेरी एक्सप्लेन एनालाइज़ करके एक्ज़ीक्यूशन प्लान वेरीफाई किया गया।", "SQL tuning"),
    BenchmarkSentence(50, "technical", "Type annotations TypeScript me runtime type safety guarantee nahi karte.", "टाइप एनोटेशन्स टाइपस्क्रिप्ट में रनटाइम टाइप सेफ्टी गारंटी नहीं करते।", "TypeScript caveat"),

    # ── Category 3: Numbers, Currency, Dates & Phone numbers (20) ──
    BenchmarkSentence(51, "numbers", "Total invoice amount ₹4,500 hai with 18% GST included.", "टोटल इनवॉइस अमाउंट ₹4,500 है विथ 18% जीएसटी इनक्लूडेड।", "Invoice & GST"),
    BenchmarkSentence(52, "numbers", "Flight 15th August ko subah 6:30 AM par depart hogi.", "फ्लाइट 15 अगस्त को सुबह 6:30 बजे डिपार्ट होगी।", "Date & time"),
    BenchmarkSentence(53, "numbers", "Please mujhe 9876543210 par call back kar lena sham 5 baje.", "प्लीज मुझे 9876543210 पर कॉल बैक कर लेना शाम 5 बजे।", "Phone number"),
    BenchmarkSentence(54, "numbers", "Monthly flat rent ₹28,000 hai plus ₹2,500 maintenance charge.", "मंथली फ्लैट रेंट ₹28,000 है प्लस ₹2,500 मेंटेनेंस चार्ज।", "Rent breakdown"),
    BenchmarkSentence(55, "numbers", "Project deadline 31st October 2026 ko midnight 11:59 PM par hai.", "प्रोजेक्ट डेडलाइन 31 अक्टूबर 2026 को मिडनाइट 11:59 बजे पर है।", "Hackathon deadline"),
    BenchmarkSentence(56, "numbers", "Petrol rate kal se ₹1.50 per litre increase ho gaya hai.", "पेट्रोल रेट कल से ₹1.50 पर लीटर इनक्रीज़ हो गया है।", "Price change"),
    BenchmarkSentence(57, "numbers", "Account number 451298762341 me ₹50,000 transfer kar diye hain.", "अकाउंट नंबर 451298762341 में ₹50,000 ट्रांसफर कर दिए हैं।", "Banking transfer"),
    BenchmarkSentence(58, "numbers", "Discount coupon apply karne ke baad cart total ₹1,299 ban raha hai.", "डिस्काउंट कूपन अप्लाई करने के बाद कार्ट टोटल ₹1,299 बन रहा है।", "E-commerce price"),
    BenchmarkSentence(59, "numbers", "Meeting 3:45 PM par start hogi aur duration lagbhag 45 minutes rahegi.", "मीटिंग 3:45 बजे स्टार्ट होगी और ड्यूरेशन लगभग 45 मिनट्स रहेगी।", "Meeting schedule"),
    BenchmarkSentence(60, "numbers", "Humara office temperature 24.5 degrees Celsius set hai.", "हमारा ऑफिस टेम्परेचर 24.5 डिग्री सेल्सियस सेट है।", "Measurement"),
    BenchmarkSentence(61, "numbers", "Train PNR number 2458910243 confirm ho gaya coach B4 seat 23 par.", "ट्रेन पीएनआर नंबर 2458910243 कन्फर्म हो गया कोच बी4 सीट 23 पर।", "Railway booking"),
    BenchmarkSentence(62, "numbers", "Car speedometer 80 km per hour cross kar chuka tha highway par.", "कार स्पीडोमीटर 80 किलोमीटर पर ऑवर क्रॉस कर चुका था हाईवे पर।", "Speed limit"),
    BenchmarkSentence(63, "numbers", "Fixed deposit par annual interest rate 7.25% offer kiya ja raha hai.", "फिक्स्ड डिपॉजिट पर एनुअल इंटरेस्ट रेट 7.25% ऑफर किया जा रहा है।", "Financial rate"),
    BenchmarkSentence(64, "numbers", "OTP 849201 hai, yeh 10 minutes ke liye valid rahega.", "ओटीपी 849201 है, यह 10 मिनट्स के लिए वैलिड रहेगा।", "OTP code"),
    BenchmarkSentence(65, "numbers", "Total weight 3.5 kilograms hai baggage allowance ke andar.", "टोटल वेट 3.5 किलोग्राम्स है बैगेज अलाउंस के अंदर।", "Weight measure"),
    BenchmarkSentence(66, "numbers", "Stock price 12% rise hua hai Q3 results announce hone ke baad.", "स्टॉक प्राइस 12% राइज़ हुआ है क्यू3 रिजल्ट्स अनाउंस होने के बाद।", "Stock market"),
    BenchmarkSentence(67, "numbers", "Passport expiry date 14th March 2032 show ho rahi hai.", "पासपोर्ट एक्सपायरी डेट 14 मार्च 2032 शो हो रही है।", "Document date"),
    BenchmarkSentence(68, "numbers", "Speed test me download bandwidth 150 Mbps record hui.", "स्पीड टेस्ट में डाउनलोड बैंडविड्थ 150 एमबीपीएस रिकॉर्ड हुई।", "Internet bandwidth"),
    BenchmarkSentence(69, "numbers", "Electricity bill is month ₹3,420 aaya hai air conditioning use ki wajah se.", "इलेक्ट्रिसिटी बिल इस मंथ ₹3,420 आया है एयर कंडीशनिंग यूज़ की वजह से।", "Utility bill"),
    BenchmarkSentence(70, "numbers", "Pin code 380015 Ahmedabad area belong karta hai.", "पिन कोड 380015 अहमदाबाद एरिया बिलॉन्ग करता है।", "Postal code"),

    # ── Category 4: Indian names, Brands & Places (15) ──
    BenchmarkSentence(71, "names", "Manav Ahmedabad se connect kar raha hai via Google Meet.", "मानव अहमदाबाद से कनेक्ट कर रहा है वाया गूगल मीट।", "Builder name & city"),
    BenchmarkSentence(72, "names", "Aarav Sharma ne Bengaluru me Swiggy aur Zomato me apply kiya.", "आरव शर्मा ने बेंगलुरु में स्विगी और ज़ोमैटो में अप्लाई किया।", "Names & food apps"),
    BenchmarkSentence(73, "names", "Pooja Patel ne Gandhinagar me TCS join kar liya hai.", "पूजा पटेल ने गांधीनगर में टीसीएस जॉइन कर लिया है।", "Gujarat names & IT"),
    BenchmarkSentence(74, "names", "Rohan Verma ne Delhi se Mumbai Indigo flight book ki.", "रोहन वर्मा ने दिल्ली से मुंबई इंडिगो फ्लाइट बुक की।", "Cities & airline"),
    BenchmarkSentence(75, "names", "Symphony aur Bolna Voice AI buildathon organize kar rahe hain.", "सिम्फनी और बोलना वॉयस एआई बिल्डाथॉन ऑर्गेनाइज़ कर रहे हैं।", "Hackathon sponsors"),
    BenchmarkSentence(76, "names", "Reliance Jio aur Airtel 5G network expand kar rahe hain Gujarat me.", "रिलायंस जियो और एयरटेल 5जी नेटवर्क एक्सपैंड कर रहे हैं गुजरात में।", "Telecom brands"),
    BenchmarkSentence(77, "names", "Infosys campus Pune me bohot picturesque design kiya gaya hai.", "इन्फोसिस कैंपस पुणे में बहुत पिक्चरेस्क डिज़ाइन किया गया है।", "Campus & place"),
    BenchmarkSentence(78, "names", "HDFC Bank netbanking portal authenticate karne me issue aa raha hai.", "एचडीएफसी बैंक नेटबैंकिंग पोर्टल ऑथेंटिकेट करने में इशू आ रहा है।", "Bank brand"),
    BenchmarkSentence(79, "names", "Ananya Deshmukh Hyderabad me Microsoft office me kaam karti hai.", "अनन्या देशमुख हैदराबाद में माइक्रोसॉफ्ट ऑफिस में काम करती है।", "Name & company"),
    BenchmarkSentence(80, "names", "Flipkart Big Billion Days sale agle hafte live hogi.", "फ्लिपकार्ट बिग बिलियन डेज़ सेल अगले हफ्ते लाइव होगी।", "Brand sale"),
    BenchmarkSentence(81, "names", "Vikram Rathore ne Jaipur se handmade craft business start kiya.", "विक्रम राठौर ने जयपुर से हैंडमेड क्राफ्ट बिज़नेस स्टार्ट किया।", "Name & heritage city"),
    BenchmarkSentence(82, "names", "Tata Motors electric vehicles segment me market leader ban gaya hai.", "टाटा मोटर्स इलेक्ट्रिक व्हीकल्स सेगमेंट में मार्केट लीडर बन गया है।", "Auto brand"),
    BenchmarkSentence(83, "names", "Bhopal aur Indore Clean City rankings me consistently top karte hain.", "भोपाल और इंदौर क्लीन सिटी रैंकिंग्स में कंसिस्टेंटली टॉप करते हैं।", "Indian cities"),
    BenchmarkSentence(84, "names", "Siddharth Mehta ne IIT Bombay se computer science complete kiya.", "सिद्धार्थ मेहता ने आईआईटी बॉम्बे से कंप्यूटर साइंस कम्प्लीट किया।", "Name & institute"),
    BenchmarkSentence(85, "names", "Paytm UPI transaction instantly complete ho jata hai bina delay ke.", "पेटीएम यूपीआई ट्रांजैक्शन इंस्टैंटली कम्प्लीट हो जाता है बिना डिले के।", "Fintech brand"),

    # ── Category 5: Mid-sentence Code-switching (15) ──
    BenchmarkSentence(86, "codeswitch", "Honestly speaking, mujhe lagta hai architecture thoda over-engineered hai.", "ऑनेस्टली स्पीकिंग, मुझे लगता है आर्किटेक्चर थोड़ा ओवर-इंजीनियर्ड है।", "Technical appraisal"),
    BenchmarkSentence(87, "codeswitch", "Please ensure karna ki production database backup ready rahe before migration.", "प्लीज एन्श्योर करना कि प्रोडक्शन डेटाबेस बैकअप रेडी रहे बिफोर माइग्रेशन।", "Pre-migration caution"),
    BenchmarkSentence(88, "codeswitch", "Maine client ko politely explain kiya that this feature is out of scope.", "मैंने क्लाइंट को पोलाइटली एक्सप्लेन किया दैट दिस फीचर इज़ आउट ऑफ स्कोप।", "Scope management"),
    BenchmarkSentence(89, "codeswitch", "At the end of the day, quality deliver karna hi hamari top priority hai.", "एट द एंड ऑफ द डे, क्वालिटी डिलीवर करना ही हमारी टॉप प्रायोरिटी है।", "Quality ethos"),
    BenchmarkSentence(90, "codeswitch", "By the way, kya aapne documentation thoroughly review kiya hai?", "बाई द वे, क्या आपने डॉक्यूमेंटेशन थरौली रिव्यू किया है?", "Query"),
    BenchmarkSentence(91, "codeswitch", "I completely agree with you ki code refactoring bohot urgently required hai.", "आई कम्प्लीटली अग्री विथ यू कि कोड रीफैक्टरिंग बहुत अर्जेंटली रिक्वायर्ड है।", "Refactoring consensus"),
    BenchmarkSentence(92, "codeswitch", "To be frank, initial prototype dekh kar stakeholders bohot impressed the.", "टू बी फ्रैंक, इनिशियल प्रोटोटाइप देख कर स्टेकहोल्डर्स बहुत इम्प्रेस्ड थे।", "Stakeholder feedback"),
    BenchmarkSentence(93, "codeswitch", "You should take care ki memory usage threshold cross na kare under heavy load.", "यू शुड टेक केयर कि मेमोरी यूसेज थ्रेशोल्ड क्रॉस ना करे अंडर हैवी लोड।", "Load constraint"),
    BenchmarkSentence(94, "codeswitch", "First of all, hume core user requirements identify karne padenge.", "फर्स्ट ऑफ ऑल, हमें कोर यूजर रिक्वायरमेंट्स आइडेंटिफाई करने पड़ेंगे।", "Product prioritization"),
    BenchmarkSentence(95, "codeswitch", "As far as I know, unka deployment schedule Friday evening fix hai.", "एज़ फार एज़ आई नो, उनका डिप्लॉयमेंट शेड्यूल फ्राइडे इवनिंग फिक्स है।", "Deployment rumor"),
    BenchmarkSentence(96, "codeswitch", "Don't worry, hum root cause analysis conduct karke patch release kar denge.", "डोंट वरी, हम रूट कॉज़ एनालिसिस कंडक्ट करके पैच रिलीज़ कर देंगे।", "Incident response"),
    BenchmarkSentence(97, "codeswitch", "Keep in mind that user privacy aur data sovereignty compromise nahi honi chahiye.", "कीप इन माइंड दैट यूजर प्राइवेसी और डेटा सॉवरेन्टी कॉम्प्रोमाइज़ नहीं होनी चाहिए।", "Compliance mandate"),
    BenchmarkSentence(98, "codeswitch", "In my opinion, edge inference cloud latency se far better user experience deta hai.", "इन माय ओपिनियन, एज इन्फरेंस क्लाउड लेटेंसी से फार बेटर यूजर एक्सपीरियंस देता है।", "Edge vs Cloud"),
    BenchmarkSentence(99, "codeswitch", "Let's catch up tomorrow morning to align on the deliverables.", "लेट्स कैच अप टुमॉरो मॉर्निंग टू अलाइन ऑन द डिलिवरेबल्स।", "Meeting wrap-up"),
    BenchmarkSentence(100, "codeswitch", "No matter what happens, hume hackathon deadline meet karni hi padegi.", "नो मैटर व्हॉट हैपन्स, हमें हैकाथॉन डेडलाइन मीट करनी ही पड़ेगी।", "Hackathon determination"),
]


def get_sentences_by_category(category: str) -> List[BenchmarkSentence]:
    return [s for s in SENTENCES if s.category == category]


def get_all_sentences() -> List[BenchmarkSentence]:
    return SENTENCES
