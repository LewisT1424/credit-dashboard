import streamlit as st
import polars as pl
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import logging
import traceback

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Report Generation", layout="wide")

st.title("Portfolio Report Generation")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.warning("Please upload data on the Home page first")
    st.stop()

df = st.session_state.portfolio_data

# ==================== REPORT CONFIGURATION ====================

st.subheader("Report Configuration")

col1, col2 = st.columns(2)

with col1:
    report_type = st.selectbox(
        "Select Report Type",
        options=["Executive Summary", "Portfolio Overview", "Risk Analysis", "Watch List Report", "Comprehensive Report"],
        index=0
    )

with col2:
    report_date = st.date_input("Report Date", datetime.now().date())

# Report sections to include
st.write("**Include in Report:**")
col1, col2, col3 = st.columns(3)

with col1:
    include_portfolio_summary = st.checkbox("Portfolio Summary", value=True)
    include_risk_metrics = st.checkbox("Risk Metrics", value=True)
    include_ratings = st.checkbox("Credit Rating Analysis", value=True)

with col2:
    include_sectors = st.checkbox("Sector Analysis", value=True)
    include_maturity = st.checkbox("Maturity Profile", value=True)
    include_borrowers = st.checkbox("Top Borrowers", value=True)

with col3:
    include_watch_list = st.checkbox("Watch List Summary", value=True)
    include_recommendations = st.checkbox("Recommendations", value=True)
    include_tables = st.checkbox("Detailed Tables", value=True)

# ==================== PDF GENERATION FUNCTIONS ====================

def get_portfolio_summary_data(df):
    """Generate portfolio summary metrics"""
    total_loans = len(df)
    total_exposure = df.select(pl.col('amount').sum()).item()
    avg_rate = df.select(pl.col('rate').mean()).item()
    
    performing = len(df.filter(pl.col('status') == 'Performing'))
    watch_list = len(df.filter(pl.col('status') == 'Watch List'))
    defaulted = len(df.filter(pl.col('status') == 'Defaulted'))
    
    return {
        'total_loans': total_loans,
        'total_exposure': total_exposure,
        'avg_rate': avg_rate,
        'performing': performing,
        'watch_list': watch_list,
        'defaulted': defaulted,
        'num_borrowers': df.select('borrower').n_unique(),
        'num_sectors': df.select('sector').n_unique()
    }

def get_risk_summary_data(df):
    """Generate risk summary metrics"""
    investment_grade = len(df.filter(pl.col('credit_rating').is_in(['A', 'A-', 'BBB+', 'BBB', 'BBB-'])))
    upper_spec = len(df.filter(pl.col('credit_rating').is_in(['BB+', 'BB', 'BB-'])))
    lower_spec = len(df.filter(pl.col('credit_rating').is_in(['B+', 'B', 'B-', 'CCC+', 'CCC', 'D'])))
    
    return {
        'investment_grade': investment_grade,
        'upper_spec': upper_spec,
        'lower_spec': lower_spec,
        'avg_rating': df.select('credit_rating').n_unique()
    }

def create_pdf_report(df, report_type, report_date, include_sections):
    """Create PDF report with selected sections"""
    
    # Create BytesIO buffer for PDF
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for PDF elements
    elements = []
    
    # Get sample styles
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        spaceBefore=12,
        borderColor=colors.HexColor('#1f77b4'),
        borderWidth=2,
        borderPadding=8
    )
    
    # ==================== TITLE PAGE ====================
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"<b>{report_type}</b>", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(f"Portfolio Analysis Report", subtitle_style))
    elements.append(Paragraph(f"As of {report_date.strftime('%B %d, %Y')}", subtitle_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # ==================== EXECUTIVE SUMMARY ====================
    
    if include_sections.get('include_portfolio_summary', True):
        elements.append(Paragraph("Executive Summary", heading_style))
        
        summary_data = get_portfolio_summary_data(df)
        
        summary_text = f"""
        <b>Portfolio Overview:</b><br/>
        This report provides a comprehensive analysis of the credit portfolio as of {report_date.strftime('%B %d, %Y')}. 
        The portfolio consists of {summary_data['total_loans']} loans with a total exposure of £{summary_data['total_exposure']/1e6:.1f}M 
        across {summary_data['num_borrowers']} borrowers in {summary_data['num_sectors']} sectors. 
        The weighted average interest rate is {summary_data['avg_rate']:.2f}%.<br/><br/>
        
        <b>Portfolio Health:</b><br/>
        {summary_data['performing']} loans ({summary_data['performing']/summary_data['total_loans']*100:.1f}%) are performing as expected,
        {summary_data['watch_list']} loans ({summary_data['watch_list']/summary_data['total_loans']*100:.1f}%) are on the watch list,
        and {summary_data['defaulted']} loans ({summary_data['defaulted']/summary_data['total_loans']*100:.1f}%) have defaulted.
        """
        
        elements.append(Paragraph(summary_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
    
    # ==================== PORTFOLIO SUMMARY TABLE ====================
    
    if include_sections.get('include_tables', True):
        elements.append(Paragraph("Portfolio Summary Metrics", heading_style))
        
        summary_data = get_portfolio_summary_data(df)
        
        summary_table_data = [
            ['Metric', 'Value'],
            ['Total Loans', str(summary_data['total_loans'])],
            ['Total Exposure', f"£{summary_data['total_exposure']/1e6:.1f}M"],
            ['Average Interest Rate', f"{summary_data['avg_rate']:.2f}%"],
            ['Number of Borrowers', str(summary_data['num_borrowers'])],
            ['Number of Sectors', str(summary_data['num_sectors'])],
            ['Performing Loans', f"{summary_data['performing']} ({summary_data['performing']/summary_data['total_loans']*100:.1f}%)"],
            ['Watch List Loans', f"{summary_data['watch_list']} ({summary_data['watch_list']/summary_data['total_loans']*100:.1f}%)"],
            ['Defaulted Loans', f"{summary_data['defaulted']} ({summary_data['defaulted']/summary_data['total_loans']*100:.1f}%)"],
        ]
        
        summary_table = Table(summary_table_data, colWidths=[3.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # ==================== RISK ANALYSIS ====================
    
    if include_sections.get('include_risk_metrics', True):
        elements.append(PageBreak())
        elements.append(Paragraph("Risk Analysis", heading_style))
        
        risk_data = get_risk_summary_data(df)
        
        risk_text = f"""
        <b>Credit Quality Distribution:</b><br/>
        The portfolio's credit quality is distributed as follows:<br/>
        • Investment Grade (A to BBB-): {risk_data['investment_grade']} loans ({risk_data['investment_grade']/len(df)*100:.1f}%)<br/>
        • Upper Speculative (BB+ to BB-): {risk_data['upper_spec']} loans ({risk_data['upper_spec']/len(df)*100:.1f}%)<br/>
        • Lower Speculative/Defaulted (B+ and below): {risk_data['lower_spec']} loans ({risk_data['lower_spec']/len(df)*100:.1f}%)<br/>
        """
        
        elements.append(Paragraph(risk_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # ==================== CREDIT RATING TABLE ====================
    
    if include_sections.get('include_ratings', True):
        elements.append(Paragraph("Credit Rating Distribution", heading_style))
        
        rating_order = ['A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC+', 'CCC', 'D']
        
        rating_table_data = [['Rating', 'Count', 'Exposure (£M)', '% of Portfolio']]
        
        total_exposure = df.select(pl.col('amount').sum()).item()
        
        for rating in rating_order:
            filtered = df.filter(pl.col('credit_rating') == rating)
            if len(filtered) > 0:
                count = len(filtered)
                exposure = filtered.select(pl.col('amount').sum()).item()
                pct = (exposure / total_exposure) * 100
                rating_table_data.append([rating, str(count), f"{exposure/1e6:.1f}", f"{pct:.1f}%"])
        
        rating_table = Table(rating_table_data, colWidths=[1.5*inch, 1.5*inch, 1.75*inch, 1.75*inch])
        rating_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(rating_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # ==================== SECTOR ANALYSIS ====================
    
    if include_sections.get('include_sectors', True):
        elements.append(PageBreak())
        elements.append(Paragraph("Sector Analysis", heading_style))
        
        sector_dist = df.group_by('sector').agg(
            pl.col('loan_id').count().alias('count'),
            pl.col('amount').sum().alias('exposure')
        ).sort('exposure', descending=True)
        
        sector_table_data = [['Sector', 'Loans', 'Exposure (£M)', '% of Portfolio']]
        
        total_exposure = df.select(pl.col('amount').sum()).item()
        
        for row in sector_dist.to_dicts():
            sector = row['sector']
            count = row['count']
            exposure = row['exposure']
            pct = (exposure / total_exposure) * 100
            sector_table_data.append([sector, str(count), f"{exposure/1e6:.1f}", f"{pct:.1f}%"])
        
        sector_table = Table(sector_table_data, colWidths=[2.0*inch, 1.25*inch, 1.75*inch, 1.5*inch])
        sector_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(sector_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # ==================== TOP BORROWERS ====================
    
    if include_sections.get('include_borrowers', True):
        elements.append(Paragraph("Top 10 Borrowers", heading_style))
        
        borrower_exp = df.group_by('borrower').agg(
            pl.col('loan_id').count().alias('count'),
            pl.col('amount').sum().alias('exposure')
        ).sort('exposure', descending=True).head(10)
        
        borrower_table_data = [['Borrower', 'Loans', 'Exposure (£M)', '% of Portfolio']]
        
        total_exposure = df.select(pl.col('amount').sum()).item()
        
        for row in borrower_exp.to_dicts():
            borrower = row['borrower']
            count = row['count']
            exposure = row['exposure']
            pct = (exposure / total_exposure) * 100
            borrower_table_data.append([borrower, str(count), f"{exposure/1e6:.1f}", f"{pct:.1f}%"])
        
        borrower_table = Table(borrower_table_data, colWidths=[2.5*inch, 1.0*inch, 1.5*inch, 1.5*inch])
        borrower_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(borrower_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # ==================== WATCH LIST ====================
    
    if include_sections.get('include_watch_list', True):
        elements.append(PageBreak())
        elements.append(Paragraph("Watch List Summary", heading_style))
        
        watch_list_df = df.filter(pl.col('status') == 'Watch List')
        
        if len(watch_list_df) > 0:
            watch_text = f"""
            <b>Watch List Overview:</b><br/>
            There are currently {len(watch_list_df)} loans on the watch list representing 
            £{watch_list_df.select(pl.col('amount').sum()).item()/1e6:.1f}M 
            ({len(watch_list_df)/len(df)*100:.1f}% of portfolio).<br/>
            """
            
            elements.append(Paragraph(watch_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Watch list loans table
            watch_table_data = [['Loan ID', 'Borrower', 'Exposure (£M)', 'Rating', 'Maturity']]
            
            for row in watch_list_df.head(15).to_dicts():
                watch_table_data.append([
                    row['loan_id'],
                    row['borrower'],
                    f"{row['amount']/1e6:.1f}",
                    row['credit_rating'],
                    row['maturity_date']
                ])
            
            watch_table = Table(watch_table_data, colWidths=[1.0*inch, 1.75*inch, 1.25*inch, 0.75*inch, 1.25*inch])
            watch_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6b6b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(watch_table)
        else:
            elements.append(Paragraph("<b>✓ No loans currently on watch list</b>", styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
    
    # ==================== RECOMMENDATIONS ====================
    
    if include_sections.get('include_recommendations', True):
        elements.append(PageBreak())
        elements.append(Paragraph("Recommendations", heading_style))
        
        risk_data = get_risk_summary_data(df)
        watch_list_df = df.filter(pl.col('status') == 'Watch List')
        
        recommendations = []
        
        if risk_data['lower_spec'] > len(df) * 0.15:
            recommendations.append("• Monitor speculative-grade loans closely - consider increasing loan loss provisions")
        
        if len(watch_list_df) > 0:
            recommendations.append("• Develop action plans for all watch list loans - prioritize near-term maturities")
        
        borrower_exp = df.group_by('borrower').agg(pl.col('amount').sum()).sort('amount', descending=True)
        if len(borrower_exp) > 0:
            top_borrower_row = borrower_exp.row(0, named=True)
            top_exp = top_borrower_row['amount']
            total = df.select(pl.col('amount').sum()).item()
            if (top_exp / total) > 0.15:
                recommendations.append("• Diversify borrower concentration - top borrower exceeds 15% threshold")
        
        if not recommendations:
            recommendations.append("• Portfolio is well-balanced with appropriate risk controls in place")
        
        for rec in recommendations:
            elements.append(Paragraph(rec, styles['Normal']))
        
        elements.append(Spacer(1, 0.3*inch))
    
    # ==================== FOOTER ====================
    
    elements.append(Spacer(1, 0.5*inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph(f"Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", footer_style))
    elements.append(Paragraph("Credit Portfolio Management System", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    return pdf_buffer.getvalue()

# ==================== GENERATE & DOWNLOAD ====================

st.subheader("Generate Report")

if st.button("Generate PDF Report", key="generate_pdf"):
    with st.spinner("Generating PDF report..."):
        try:
            pdf_data = create_pdf_report(
                df,
                report_type,
                report_date,
                {
                    'include_portfolio_summary': include_portfolio_summary,
                    'include_risk_metrics': include_risk_metrics,
                    'include_ratings': include_ratings,
                    'include_sectors': include_sectors,
                    'include_maturity': include_maturity,
                    'include_borrowers': include_borrowers,
                    'include_watch_list': include_watch_list,
                    'include_recommendations': include_recommendations,
                    'include_tables': include_tables
                }
            )
            
            # Download button
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"Portfolio_Report_{report_type.replace(' ', '_')}_{report_date}.pdf",
                mime="application/pdf",
                key="download_pdf"
            )
            
            st.success("✅ PDF report generated successfully!")
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            st.error(f"Error generating PDF: {error_msg}")
            st.error(f"Error Type: {error_type}")
            
            # Detailed debugging information
            with st.expander("🔍 Debugging Information"):
                st.write(f"**Error Message:** {error_msg}")
                st.write(f"**Error Type:** {error_type}")
                st.write(f"**Stack Trace:**")
                import traceback
                st.code(traceback.format_exc())
                
                # Debug summary data
                st.write("**Summary Data Types:**")
                summary_data = get_portfolio_summary_data(df)
                for key, value in summary_data.items():
                    st.write(f"  - {key}: {type(value).__name__} = {value}")
                
                st.write("**Risk Data Types:**")
                risk_data = get_risk_summary_data(df)
                for key, value in risk_data.items():
                    st.write(f"  - {key}: {type(value).__name__} = {value}")
            
            logger.error(f"PDF generation error ({error_type}): {error_msg}")
            logger.error(traceback.format_exc())

st.info("💡 Select report type and sections, then click 'Generate PDF Report' to create a downloadable report for stakeholders.")
