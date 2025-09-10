#!/usr/bin/env python3
"""
🚀 AI Customer Feedback Analyzer - Professional Launch Script
"""
import os
import sys
import time
import webbrowser
import threading

def print_welcome():
    print("🤖 AI CUSTOMER FEEDBACK ANALYZER")
    print("=" * 60)
    print("🎨 Professional Web Interface Edition")
    print("🏆 Production-Ready AI Service")
    print()

def print_features():
    print("✨ FEATURES:")
    print("   🖥️  Beautiful modern web dashboard") 
    print("   📊 Real-time analytics and statistics")
    print("   🔍 Interactive sentiment analysis")
    print("   📋 Batch processing with visual results")
    print("   🎯 One-click sample data testing")
    print("   📱 Mobile-responsive design")
    print("   ⚡ Live API health monitoring")
    print("   🎨 Professional animations & styling")
    print()

def print_urls():
    print("🌐 ACCESS POINTS:")
    print("   🏠 Main Dashboard: http://localhost:5000")
    print("   📊 Live Statistics: http://localhost:5000 (integrated)")
    print("   🏥 Health Check: http://localhost:5000/health") 
    print("   📡 API Docs: http://localhost:5000/api")
    print()

def print_testing():
    print("🧪 TESTING:")
    print("   • Use sample data buttons for instant results")
    print("   • Try single analysis with custom text")
    print("   • Test batch processing with multiple reviews")
    print("   • Run: python test_api.py")
    print()

def open_browser_delayed():
    """Open browser after a short delay"""
    time.sleep(3)
    try:
        webbrowser.open('http://localhost:5000')
        print("🌐 Browser opened automatically!")
    except Exception:
        print("💡 Manually open: http://localhost:5000")

def main():
    print_welcome()
    print_features()
    print_urls()
    print_testing()

    print("🚀 LAUNCHING IN 3 SECONDS...")
    print("   (Browser will open automatically)")
    print("   Press Ctrl+C to cancel")
    print()

    # Start browser opener in background
    browser_thread = threading.Thread(target=open_browser_delayed)
    browser_thread.daemon = True
    browser_thread.start()

    try:
        time.sleep(3)

        # Import and run the Flask app
        print("🔥 Starting Flask application...")
        import app
        app.app.run(host='0.0.0.0', port=5000, debug=False)

    except KeyboardInterrupt:
        print("\n\n👋 Application stopped")
        print("\n🎉 Thank you for using AI Customer Feedback Analyzer!")
        print("   Perfect for your portfolio! 🎯")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Try manual start: python app.py")

if __name__ == "__main__":
    main()
