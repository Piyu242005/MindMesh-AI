## Complete Workflow of Your RAG System (Step-by-Step)

Below is the **full pipeline from video → chatbot answer**, explained simply.

---

## Step 1: Input Video Processing

![Image](https://resource.flexclip.com/pages/learn-center/add-audio-waveform-to-videos/convert-audio-to-audio-waveform.webp)

![Image](https://miro.medium.com/1%2AKnY7dlToDXNj2dDzmkskXw.gif)

![Image](https://helpx-prod.scene7.com/is/image/HelpxProd/ed01?%24png%24=\&jpegSize=100\&wid=444)

![Image](https://images.ctfassets.net/lzny33ho1g45/78HJAckzlbJ3N2AWZDRw0v/6ac76d7b710c200e006bfd1655f56aeb/image3.jpeg)

**What happens:**

1. **video_to_mp3.py**

   * Converts video → audio (MP3)

2. **mp3_to_json.py**

   * Converts audio → text using speech-to-text
   * Saves transcript in JSON format with timestamps

**Output:**

```
transcript.json
```

---

## Step 2: Text Cleaning and Chunking

![Image](https://www.researchgate.net/publication/286746122/figure/fig2/AS%3A784495364026368%401564049678217/Text-Chunking-Pipeline-A-text-chunker-is-implemented-as-a-pipeline-of-various-NLP.png)

![Image](https://www.researchgate.net/publication/354392398/figure/fig1/AS%3A1065241240678401%401630984711359/sualization-of-how-sliding-window-was-used-for-data-overlapping-for-creation-of-the.ppm)

![Image](https://miro.medium.com/v2/resize%3Afit%3A1400/0%2A4dAo2eyWJOqHzKzt)

![Image](https://substackcdn.com/image/fetch/%24s_%21tmOD%21%2Cf_auto%2Cq_auto%3Agood%2Cfl_progressive%3Asteep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fa6ad83a6-2879-4c77-9e49-393f16577aef_1066x288.gif)

**What happens:**

* Clean text (remove duplicates, noise)
* Split text into small chunks
* Add overlap to preserve context

**Example:**

```
Chunk 1: AI is transforming industries...
Chunk 2: ...transforming industries like healthcare...
```

**Why:** Improves search accuracy

---

## Step 3: Create Embeddings and Store in Database

![Image](https://miro.medium.com/v2/resize%3Afit%3A1212/1%2AprZlvFpSvsxM8nySxtXf1Q.png)

![Image](https://cdn.prod.website-files.com/63ccf2f0ea97be12ead278ed/646c34aac1ee63426e84725f_Learn%20about%20Vector%20Database%20%281%29.png)

![Image](https://timescale.ghost.io/blog/content/images/size/w1000/2025/01/What-Is-Semantic-Search-with-Filters-and-How-to-Implement-It-with-pgvector-and-Python_with-filters-1.png)

![Image](https://cdn.prod.website-files.com/640248e1fd70b63c09bd3d09/653fd23f1565c0c1da063efc_Semantic%20Search%20Text%20Embeddings%20%281%29.png)

**What happens:**

* Convert text chunks → embeddings (numerical vectors)
* Store in **ChromaDB vector database**

**Result:**

```
Database contains semantic meaning of text
```

---

## Step 4: User Asks Question

![Image](https://sendbird.imgix.net/cms/Chatbot-UI.webp)

![Image](https://images.openai.com/static-rsc-3/3gL1g31H56s57DLOpmFa7EqQzBf9vbOTYw54Vl5gMWEIlr1Qj523NiijZg4AX3KBrib6nWxhEdggb9a0iGp2oSmK2oQhZxhfM0ASmJKq-Kc?purpose=fullsize\&v=1)

![Image](https://global.discourse-cdn.com/streamlit/optimized/2X/1/1c3534b3700888360426b38076a3d2e639c90c64_2_690x388.png)

![Image](https://global.discourse-cdn.com/streamlit/optimized/3X/1/9/19b9226792f6ddfb70b38e2797f7840eb301efe5_2_690x362.png)

Example user question:

```
"What is machine learning?"
```

System converts question → embedding

---

## Step 5: Hybrid Search (Find Best Answer)

![Image](https://media2.dev.to/dynamic/image/width%3D1280%2Cheight%3D720%2Cfit%3Dcover%2Cgravity%3Dauto%2Cformat%3Dauto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fvibuhf1961cm7e8ebn52.png)

![Image](https://docs.weaviate.io/assets/images/bm25_operators_light-fe6a283b72823515e7f70dc0a6fc6d29.png)

![Image](https://miro.medium.com/0%2AlUCtODvBQ6xJAAhc.png)

![Image](https://media.licdn.com/dms/image/v2/D5612AQGDJhVMrRaq0g/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1707196495204?e=2147483647\&t=JfM6lL9xCqg7Vi5tJS8sT5klUUkQlLbqIgdgq2oAlgk\&v=beta)

System performs:

* Vector search (semantic similarity)
* BM25 keyword search
* Hybrid fusion (combines both)
* Reranking using cross-encoder

**Result:** Best matching chunks found

---

## Step 6: Send Context to LLM

![Image](https://miro.medium.com/v2/resize%3Afit%3A1200/1%2A2Ai-FHeDS0dCEl4nOEryjw.png)

![Image](https://www.researchgate.net/publication/373890567/figure/fig1/AS%3A11431281210605904%401702055530589/A-general-overview-of-types-of-input-processing-methods-output-and-applications-of-AI.tif)

![Image](https://images.openai.com/static-rsc-3/T9q29aVnabRJbeWoiMfXKImS7vtO5hNgwGzFIFnLVJYDuqB0bJxmoCH8cMaHzaEraQ0vYQulq5o4au3vFZaPifDG7yaEpWwEX4Hs5Ipunyg?purpose=fullsize\&v=1)

![Image](https://substackcdn.com/image/fetch/f_auto%2Cq_auto%3Agood%2Cfl_progressive%3Asteep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fc3e159bd-1228-4205-b1eb-5898ab9172d3_1600x856.png)

System sends to LLM:

```
Question: What is machine learning?

Context:
Machine learning is a subset of AI...
```

LLM generates accurate answer.

---

## Step 7: Show Answer in Chat UI

![Image](https://global.discourse-cdn.com/streamlit/original/2X/1/1c3534b3700888360426b38076a3d2e639c90c64.png)

![Image](https://images.openai.com/static-rsc-3/jgfUyq3pfr7fLSTgApSZ_zrErFqrmVqf4GYz48092JsQpDi2QRf29_RBx_ny217hDT3sBAwHKouKAXlKvAbDyQ_qv2xtuqCcxojzEgVCpmU?purpose=fullsize\&v=1)

![Image](https://sendbird.imgix.net/cms/Chatbot-UI.webp?auto=format%2Ccompress\&crop=faces)

![Image](https://sendbird.imgix.net/cms/chatbot-user-interface-design.png)

User sees:

```
Answer:
Machine learning is a subset of AI that allows systems to learn from data.
Timestamp: 02:15
```

System also remembers conversation.

---

## Final Architecture Summary (Very Simple)

```
Video
  ↓
Audio extraction
  ↓
Speech-to-text
  ↓
Text cleaning
  ↓
Chunking
  ↓
Embeddings
  ↓
ChromaDB storage
  ↓
User question
  ↓
Hybrid search
  ↓
LLM answer generation
  ↓
Streamlit chatbot UI
```

---

## Your Project Level

This system includes:

* Vector database
* Hybrid search
* Reranking
* Prompt engineering
* Memory
* Evaluation

This is equivalent to **real-world AI Engineer / Data Scientist production system**.

---

If you want, I can also give a **perfect resume project description (ATS-optimized) for this project**.
