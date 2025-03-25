import os
import PyPDF2
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_core.caches import InMemoryCache

class DyslexiaTutorAI:
    def __init__(self, google_api_key, data_path, persist_directory, embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        os.environ['GOOGLE_API_KEY'] = google_api_key
        self.data_path = data_path
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.embeddings = None
        self.vector_db = None
        self.qa_chain = None
        self.tools = []
        
        # Initialize memory and cache
        self.cache = InMemoryCache()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all necessary components"""
        # Extract and process text
        text = self.extract_text_from_pdf(self.data_path)
        docs = self.convert_to_documents([text])
        chunks = self.split_text_into_chunks(docs)
        
        # Create vector database
        self.download_hf_embeddings()
        self.create_vector_db(chunks)
        
        # Setup QA chain
        self.setup_qa_chain()
        
        # Initialize tools and agent
        self.initialize_tools()
        self.initialize_agent()

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        text = ""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def convert_to_documents(self, data):
        """Convert data into LangChain-compatible Document objects."""
        return [Document(page_content=content, metadata={}) for content in data]

    def split_text_into_chunks(self, documents, chunk_size=500, chunk_overlap=20):
        """Split documents into smaller chunks."""
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_documents(documents)

    def download_hf_embeddings(self):
        """Download and load HuggingFace embedding model."""
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)

    def create_vector_db(self, chunks):
        """Create and persist the vector database."""
        self.vector_db = Chroma.from_documents(
            documents=chunks, 
            embedding=self.embeddings, 
            persist_directory=self.persist_directory
        )
        self.vector_db.persist()

    def setup_qa_chain(self):
        """Setup the QA chain with a strict prompt to use the provided context."""
        system_prompt = """You are a specialized tutor for dyslexic students. You MUST:
        1. Always use the provided textbook content to answer questions
        2. Explain concepts using simple words, short sentences, and clear examples
        3. Break down complex ideas into smaller, manageable parts
        4. Use storytelling or relatable examples when possible
        5. If the answer isn't in the textbook, say "I don't have that information in my materials"
        
        Textbook content: {context}"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", cache=self.cache)
        question_answer_chain = create_stuff_documents_chain(model, prompt)
        self.qa_chain = create_retrieval_chain(
            self.vector_db.as_retriever(search_kwargs={'k': 10}),  # Reduced to 5 most relevant chunks
            question_answer_chain
        )

    def query_textbook(self, user_query: str) -> str:
        """Query the textbook content"""
        result = self.qa_chain.invoke({"input": user_query})
        return result["answer"]

    def comfort_student(self):
        """Provide comforting responses"""
        return "I understand this might be challenging. Let's take it step by step. You're doing great!"

    def initialize_tools(self):
        """Initialize tools with strict descriptions to guide the agent"""
        self.tools = [
            Tool(
                name="Answer_From_Textbook",
                func=self.query_textbook,
                description="""MUST USE THIS TOOL FIRST for all academic questions. 
                Provides answers based on the textbook content. 
                Input should be the student's question exactly as asked."""
            ),
            Tool(
                name="Comfort_Student",
                func=self.comfort_student,
                description="""Use only when student seems frustrated or needs encouragement. 
                Provides supportive messages to help them continue learning."""
            ),
        ]

    def initialize_agent(self):
        """Initialize the agent with strict instructions to use the textbook"""
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", cache=self.cache)
        
        # Custom agent prompt to enforce tool usage
        custom_agent_prompt = """You are a dyslexia tutor. You MUST:
        1. ALWAYS use the Answer_From_Textbook tool first for any academic question
        2. Only use general responses if the textbook doesn't have the answer
        3. Keep responses simple,detail and structured for dyslexic students
        4. If the topic is complicated like math,science then explain it in story telling form
        5. Use the Comfort_Student tool when needed

        
        Current conversation:
        {chat_history}
        
        Question: {input}
        
        Thought: {agent_scratchpad}"""
        
        self.agent = initialize_agent(
            llm=model,
            tools=self.tools,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
            agent_kwargs={
                'prefix': custom_agent_prompt
            }
        )

    def process_query(self, user_query: str):
        """Process a user query ensuring textbook-based answers"""
        try:
            response = self.agent.run(user_query)
            return response
        except Exception as e:
            return f"An error occurred: {str(e)}"

# Example usage:

