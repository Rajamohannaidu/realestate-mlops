# src/chatbot.py

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.schema import HumanMessage, AIMessage

load_dotenv()

class RealEstateInvestmentChatbot:
    """
    Conversational AI Assistant for Real Estate Investment Guidance
    Powered by LangChain and Groq Cloud LLM
    """
    
    def __init__(self, api_key=None):
        """Initialize the chatbot with Groq LLM"""
        
        if api_key is None:
            api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Please set it in .env file")
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            temperature=0.7,
            model_name="llama-3.3-70b-versatile",  # or "llama2-70b-4096"
            groq_api_key=api_key
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Create system prompt
        self.system_prompt = self._create_system_prompt()
        
        # Initialize conversation chain
        self.conversation = self._initialize_conversation_chain()
        
        # Store context
        self.context = {
            'current_property': None,
            'analysis_results': None,
            'user_preferences': {}
        }
    
    def _create_system_prompt(self):
        """Create comprehensive system prompt for the assistant"""
        return """You are an expert Real Estate Investment Advisor AI Assistant. Your role is to help investors make informed decisions about property investments.

Your capabilities include:
1. Analyzing property investment opportunities
2. Explaining ROI, rental yield, cap rate, and other investment metrics
3. Providing insights on property appreciation and market trends
4. Answering questions about real estate investment strategies
5. Explaining machine learning predictions and their factors
6. Offering personalized investment recommendations

Guidelines:
- Be professional, knowledgeable, and supportive
- Explain complex financial concepts in simple terms
- Use specific numbers and data when available from context
- Provide actionable insights and recommendations
- Ask clarifying questions when needed
- Be honest about limitations and uncertainties
- Focus on long-term value and risk management
- Reference specific property details when available in context

When discussing properties:
- Always mention key metrics (ROI, yield, appreciation) if available
- Explain what influences the price prediction
- Highlight potential risks and opportunities
- Consider the investor's goals and risk tolerance

When you have specific property context (price, area, location, etc.), always reference those exact numbers in your answers.
When you have analysis results (ROI, rental yield, etc.), use those specific values to provide concrete advice.

Remember: You're here to educate and guide, not to make final decisions for users."""

    def _initialize_conversation_chain(self):
        """Initialize the conversation chain with memory"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=prompt,
            verbose=False
        )
        
        return conversation
    
    def set_property_context(self, property_data, analysis_results=None):
        """
        Set context about the current property being discussed
        """
        self.context['current_property'] = property_data
        self.context['analysis_results'] = analysis_results
    
    def get_context_summary(self):
        """Generate a summary of current context"""
        summary_parts = []
        
        if self.context.get('current_property'):
            prop = self.context['current_property']
            summary_parts.append("Current Property Information:")
            summary_parts.append(f"- Price: ₹{prop.get('price', 'N/A'):,.0f}" if isinstance(prop.get('price'), (int, float)) else f"- Price: {prop.get('price', 'N/A')}")
            if prop.get('area'):
                summary_parts.append(f"- Area: {prop.get('area')} sq ft")
            if prop.get('bedrooms'):
                summary_parts.append(f"- Bedrooms: {prop.get('bedrooms')}")
            if prop.get('bathrooms'):
                summary_parts.append(f"- Bathrooms: {prop.get('bathrooms')}")
            if prop.get('location'):
                summary_parts.append(f"- Location: {prop.get('location')}")
            if prop.get('furnishing'):
                summary_parts.append(f"- Furnishing: {prop.get('furnishing')}")
        
        if self.context.get('analysis_results'):
            analysis = self.context['analysis_results']
            summary_parts.append("\nInvestment Analysis Results:")
            
            if 'roi' in analysis:
                roi_pct = analysis['roi']['roi_percentage']
                net_profit = analysis['roi']['net_profit']
                summary_parts.append(f"- ROI: {roi_pct:.2f}% (Net Profit: ₹{net_profit:,.0f})")
            
            if 'rental_yield' in analysis:
                yield_pct = analysis['rental_yield']['net_yield_percentage']
                annual_income = analysis['rental_yield']['net_annual_income']
                summary_parts.append(f"- Net Rental Yield: {yield_pct:.2f}% (₹{annual_income:,.0f}/year)")
            
            if 'cap_rate' in analysis:
                cap_rate = analysis['cap_rate']['cap_rate_percentage']
                summary_parts.append(f"- Cap Rate: {cap_rate:.2f}%")
            
            if 'cash_flow' in analysis:
                annual_cf = analysis['cash_flow']['annual_cash_flow']
                monthly_cf = analysis['cash_flow']['monthly_cash_flow']
                summary_parts.append(f"- Cash Flow: ₹{annual_cf:,.0f}/year (₹{monthly_cf:,.0f}/month)")
        
        return "\n".join(summary_parts) if summary_parts else ""
    
    def chat(self, user_message):
        """
        Process user message and return AI response with context
        """
        try:
            # Get context summary
            context_info = self.get_context_summary()
            
            # Enhance message with context if available
            if context_info:
                enhanced_message = f"{user_message}\n\n[Context Information:\n{context_info}]"
            else:
                enhanced_message = user_message
            
            # Get response from LLM
            response = self.conversation.predict(input=enhanced_message)
            
            return response
        
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."
    
    def _enhance_message_with_context(self, user_message):
        """
        Add relevant context to user message (deprecated - now using get_context_summary)
        """
        return user_message
    
    def explain_prediction(self, property_features, predicted_price, explanation_data):
        """
        Generate explanation for a price prediction
        """
        explanation_text = f"""
The predicted price for this property is ${predicted_price:,.2f}.

Here are the key factors influencing this prediction:

"""
        
        if explanation_data and isinstance(explanation_data, dict):
            for i, (feature, data) in enumerate(list(explanation_data.items())[:5], 1):
                if isinstance(data, dict) and 'shap_value' in data:
                    impact = data['shap_value']
                    value = data['feature_value']
                    direction = "increases" if impact > 0 else "decreases"
                    explanation_text += f"{i}. {feature} ({value:.2f}): {direction} price by ${abs(impact):,.2f}\n"
        
        message = f"Please explain this property price prediction in simple terms:\n{explanation_text}"
        
        return self.chat(message)
    
    def get_investment_advice(self, analysis_results):
        """
        Get personalized investment advice based on analysis
        """
        roi = analysis_results['roi']['roi_percentage']
        rental_yield = analysis_results['rental_yield']['net_yield_percentage']
        cash_flow = analysis_results['cash_flow']['annual_cash_flow']
        
        message = f"""
Based on the investment analysis:
- ROI: {roi:.2f}%
- Rental Yield: {rental_yield:.2f}%
- Annual Cash Flow: ${cash_flow:,.2f}

Should I invest in this property? What are the key considerations?
"""
        
        return self.chat(message)
    
    def compare_properties(self, property1_analysis, property2_analysis):
        """
        Compare two properties and provide recommendation
        """
        message = f"""
Please help me compare these two properties:

Property 1:
- ROI: {property1_analysis['roi']['roi_percentage']:.2f}%
- Rental Yield: {property1_analysis['rental_yield']['net_yield_percentage']:.2f}%
- Price: ${property1_analysis['property_price']:,.2f}

Property 2:
- ROI: {property2_analysis['roi']['roi_percentage']:.2f}%
- Rental Yield: {property2_analysis['rental_yield']['net_yield_percentage']:.2f}%
- Price: ${property2_analysis['property_price']:,.2f}

Which one would be a better investment and why?
"""
        
        return self.chat(message)
    
    def reset_conversation(self):
        """Reset conversation memory"""
        self.memory.clear()
        self.context = {
            'current_property': None,
            'analysis_results': None,
            'user_preferences': {}
        }
    
    def get_conversation_history(self):
        """Get the conversation history"""
        return self.memory.load_memory_variables({})

# Example usage
if __name__ == "__main__":
    try:
        # Initialize chatbot
        chatbot = RealEstateInvestmentChatbot()
        
        print("Real Estate Investment AI Assistant")
        print("=" * 50)
        print("Ask me anything about real estate investing!")
        print("Type 'quit' to exit\n")
        
        while True:
            user_input = input("You: ")
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Assistant: Thank you for using the Real Estate Investment Assistant. Good luck with your investments!")
                break
            
            response = chatbot.chat(user_input)
            print(f"\nAssistant: {response}\n")
    
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file with GROQ_API_KEY")
        print("2. Obtained an API key from https://console.groq.com/")
        print("\nExample .env file:")
        print("GROQ_API_KEY=your_api_key_here")