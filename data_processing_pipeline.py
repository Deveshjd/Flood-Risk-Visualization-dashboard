#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class FloodDataProcessor:
    """
    Main class for processing rainfall data and calculating flood parameters.
    """
    
    def __init__(self, rainfall_csv_path: str):
        """
        Initialize the processor with rainfall data.
        
        Args:
            rainfall_csv_path: Path to the CSV file containing rainfall data
        """
        self.rainfall_csv_path = 'district_wise_rainfall_normal.csv'
        self.df = None
        self.processed_data = []
        
    def load_data(self) -> pd.DataFrame:
        """Load rainfall data from CSV file."""
        print("📂 Loading rainfall data...")
        self.df = pd.read_csv(self.rainfall_csv_path)
        print(f"✓ Loaded {len(self.df)} districts from {self.df['STATE_UT_NAME'].nunique()} states")
        return self.df
    
    def validate_data(self) -> bool:
        """Validate that all required columns are present."""
        required_columns = [
            'STATE_UT_NAME', 'DISTRICT', 'JAN', 'FEB', 'MAR', 'APR', 
            'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'ANNUAL'
        ]
        
        missing = [col for col in required_columns if col not in self.df.columns]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
        
        print("✓ Data validation passed")
        return True
    
    def transform_data(self) -> List[Dict]:
        """
        Transform raw CSV data into structured JSON format.
        
        Returns:
            List of district dictionaries with monthly rainfall data
        """
        print("🔄 Transforming data...")
        
        self.processed_data = []
        
        for _, row in self.df.iterrows():
            district_data = {
                'state': str(row['STATE_UT_NAME']),
                'district': str(row['DISTRICT']),
                'monthly': {
                    'January': float(row['JAN']),
                    'February': float(row['FEB']),
                    'March': float(row['MAR']),
                    'April': float(row['APR']),
                    'May': float(row['MAY']),
                    'June': float(row['JUN']),
                    'July': float(row['JUL']),
                    'August': float(row['AUG']),
                    'September': float(row['SEP']),
                    'October': float(row['OCT']),
                    'November': float(row['NOV']),
                    'December': float(row['DEC'])
                },
                'annual': float(row['ANNUAL']),
                'monsoon': float(row['Jun-Sep']) if 'Jun-Sep' in row else 0.0
            }
            
            # Add calculated metrics
            district_data['metrics'] = self.calculate_district_metrics(district_data)
            
            self.processed_data.append(district_data)
        
        print(f"✓ Transformed {len(self.processed_data)} district records")
        return self.processed_data
    
    def calculate_district_metrics(self, district: Dict) -> Dict:
        """
        Calculate statistical metrics for a district.
        
        Args:
            district: District data dictionary
            
        Returns:
            Dictionary of calculated metrics
        """
        monthly_values = list(district['monthly'].values())
        
        return {
            'avg_monthly': np.mean(monthly_values),
            'max_monthly': np.max(monthly_values),
            'min_monthly': np.min(monthly_values),
            'std_monthly': np.std(monthly_values),
            'monsoon_percentage': (district['monsoon'] / district['annual'] * 100) if district['annual'] > 0 else 0,
            'peak_month': max(district['monthly'].items(), key=lambda x: x[1])[0]
        }
    
    def save_output(self, output_path: str = 'complete_rainfall_data.json'):
        """
        Save processed data to JSON file.
        
        Args:
            output_path: Path for output JSON file
        """
        print(f"💾 Saving processed data to {output_path}...")
        
        with open(output_path, 'w') as f:
            json.dump(self.processed_data, f, indent=2)
        
        print(f"✓ Data saved successfully ({len(self.processed_data)} districts)")
    
    def generate_summary_report(self) -> Dict:
        """
        Generate a summary report of the processed data.
        
        Returns:
            Dictionary containing summary statistics
        """
        states = list(set([d['state'] for d in self.processed_data]))
        
        annual_rainfall = [d['annual'] for d in self.processed_data]
        monsoon_rainfall = [d['monsoon'] for d in self.processed_data]
        
        report = {
            'total_districts': len(self.processed_data),
            'total_states': len(states),
            'states': sorted(states),
            'rainfall_statistics': {
                'annual': {
                    'mean': np.mean(annual_rainfall),
                    'median': np.median(annual_rainfall),
                    'min': np.min(annual_rainfall),
                    'max': np.max(annual_rainfall),
                    'std': np.std(annual_rainfall)
                },
                'monsoon': {
                    'mean': np.mean(monsoon_rainfall),
                    'median': np.median(monsoon_rainfall),
                    'min': np.min(monsoon_rainfall),
                    'max': np.max(monsoon_rainfall),
                    'std': np.std(monsoon_rainfall)
                }
            },
            'top_rainfall_districts': self.get_top_districts(5),
            'high_risk_districts': self.identify_high_risk_districts()
        }
        
        return report
    
    def get_top_districts(self, n: int = 5) -> List[Dict]:
        """Get top N districts by annual rainfall."""
        sorted_districts = sorted(self.processed_data, 
                                 key=lambda x: x['annual'], 
                                 reverse=True)
        
        return [{
            'district': d['district'],
            'state': d['state'],
            'annual_rainfall': d['annual']
        } for d in sorted_districts[:n]]
    
    def identify_high_risk_districts(self, threshold: float = 3000) -> List[Dict]:
        """
        Identify districts with high flood risk based on rainfall.
        
        Args:
            threshold: Annual rainfall threshold in mm
            
        Returns:
            List of high-risk districts
        """
        high_risk = [
            {
                'district': d['district'],
                'state': d['state'],
                'annual_rainfall': d['annual'],
                'monsoon_rainfall': d['monsoon']
            }
            for d in self.processed_data 
            if d['annual'] > threshold
        ]
        
        return sorted(high_risk, key=lambda x: x['annual_rainfall'], reverse=True)
    
    def print_summary(self, report: Dict):
        """Print a formatted summary report."""
        print("\n" + "="*70)
        print("📊 FLOOD DATA PROCESSING SUMMARY")
        print("="*70)
        
        print(f"\n📍 Geographic Coverage:")
        print(f"   • Total Districts: {report['total_districts']}")
        print(f"   • Total States: {report['total_states']}")
        
        print(f"\n🌧️  Rainfall Statistics (Annual):")
        annual = report['rainfall_statistics']['annual']
        print(f"   • Mean: {annual['mean']:.1f} mm")
        print(f"   • Median: {annual['median']:.1f} mm")
        print(f"   • Range: {annual['min']:.1f} - {annual['max']:.1f} mm")
        print(f"   • Std Dev: {annual['std']:.1f} mm")
        
        print(f"\n🌊 Monsoon Statistics:")
        monsoon = report['rainfall_statistics']['monsoon']
        print(f"   • Mean: {monsoon['mean']:.1f} mm")
        print(f"   • Median: {monsoon['median']:.1f} mm")
        print(f"   • Range: {monsoon['min']:.1f} - {monsoon['max']:.1f} mm")
        
        print(f"\n🏆 Top 5 High-Rainfall Districts:")
        for i, district in enumerate(report['top_rainfall_districts'], 1):
            print(f"   {i}. {district['district']}, {district['state']}: {district['annual_rainfall']:.1f} mm")
        
        print(f"\n⚠️  High-Risk Districts (>{3000} mm annual):")
        print(f"   Total: {len(report['high_risk_districts'])} districts")
        if report['high_risk_districts']:
            for district in report['high_risk_districts'][:5]:
                print(f"   • {district['district']}, {district['state']}: {district['annual_rainfall']:.1f} mm")
        
        print("\n" + "="*70)


class HydrologicalSimulator:
    """
    Hydrological simulation for flood prediction.
    """
    
    @staticmethod
    def calculate_runoff(rainfall: float, soil_type: str = 'medium') -> float:
        """
        Calculate surface runoff using SCS Curve Number method.
        
        Args:
            rainfall: Precipitation amount in mm
            soil_type: Type of soil ('high', 'medium', 'low' infiltration)
            
        Returns:
            Runoff amount in mm
        """
        # Curve numbers for different soil types
        curve_numbers = {
            'high': 85,    # Low infiltration (clay, urban)
            'medium': 70,  # Moderate infiltration (loam)
            'low': 55      # High infiltration (sand)
        }
        
        cn = curve_numbers.get(soil_type, 70)
        
        # Calculate potential maximum retention
        s = (25400 / cn) - 254  # in mm
        
        # Initial abstraction (typically 0.2 * S)
        ia = 0.2 * s
        
        # Calculate runoff
        if rainfall <= ia:
            return 0.0
        
        runoff = ((rainfall - ia) ** 2) / (rainfall - ia + s)
        return runoff
    
    @staticmethod
    def calculate_water_level(runoff: float, area_km2: float = 100) -> float:
        """
        Convert runoff to water level.
        
        Args:
            runoff: Runoff amount in mm
            area_km2: Catchment area in square kilometers
            
        Returns:
            Average water depth in meters
        """
        # Convert runoff (mm) to volume (cubic meters)
        volume_m3 = runoff * area_km2 * 1000
        
        # Calculate average depth assuming flat terrain
        # This is a simplified model; actual DEM would provide better results
        avg_depth_m = runoff / 1000  # Convert mm to meters
        
        # Apply terrain factor (concave terrain accumulates more water)
        terrain_factor = 1.5
        adjusted_depth = avg_depth_m * terrain_factor
        
        return adjusted_depth
    
    @staticmethod
    def classify_flood_risk(water_level: float, rainfall: float) -> Tuple[str, int]:
        """
        Classify flood risk based on water level and rainfall.
        
        Args:
            water_level: Water level in meters
            rainfall: Rainfall in mm
            
        Returns:
            Tuple of (risk_level_string, risk_level_numeric)
        """
        if water_level > 4.0 or rainfall > 500:
            return 'EXTREME', 4
        elif water_level > 2.5 or rainfall > 350:
            return 'HIGH', 3
        elif water_level > 1.5 or rainfall > 200:
            return 'MEDIUM', 2
        else:
            return 'LOW', 1
    
    @staticmethod
    def simulate_flood_progression(rainfall: float, duration_hours: int = 72) -> List[float]:
        """
        Simulate flood water level progression over time.
        
        Args:
            rainfall: Total rainfall in mm
            duration_hours: Simulation duration in hours
            
        Returns:
            List of water levels for each hour
        """
        water_levels = []
        
        for hour in range(duration_hours + 1):
            progress = hour / duration_hours
            
            # Peak at 70% of duration
            peak_time = 0.7
            
            if progress < peak_time:
                # Rising phase (exponential growth)
                level = (rainfall / 100) * (progress / peak_time) ** 1.5
            else:
                # Recession phase (exponential decay)
                recession_factor = (progress - peak_time) / (1 - peak_time)
                level = (rainfall / 100) * (1 - recession_factor) ** 2
            
            # Add random variation (±10%)
            level += level * np.random.uniform(-0.1, 0.1)
            water_levels.append(max(0, level))
        
        return water_levels


def main():
    """Main execution function."""
    
    print("\n🌊 FLOOD VISUALIZATION DASHBOARD - DATA PROCESSOR")
    print("=" * 70 + "\n")
    
    # Initialize processor
    input_file = '/mnt/user-data/uploads/district_wise_rainfall_normal.csv'
    processor = FloodDataProcessor(input_file)
    
    # Load and validate data
    processor.load_data()
    
    if not processor.validate_data():
        print("❌ Data validation failed. Exiting.")
        return
    
    # Transform data
    processor.transform_data()
    
    # Save processed data
    processor.save_output('./complete_rainfall_data.json')
    
    # Generate and display summary report
    report = processor.generate_summary_report()
    processor.print_summary(report)
    
    # Save summary report
    with open('./summary_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n✨ Processing complete!")
    print("📁 Output files:")
    print("   • complete_rainfall_data.json - Full processed dataset")
    print("   • summary_report.json - Statistical summary")
    
    # Demonstrate hydrological simulation
    print("\n" + "="*70)
    print("🧪 HYDROLOGICAL SIMULATION DEMO")
    print("="*70)
    
    simulator = HydrologicalSimulator()
    
    # Example: Heavy monsoon rainfall
    test_rainfall = 450  # mm
    print(f"\n📊 Simulating flood for {test_rainfall} mm rainfall:")
    
    runoff = simulator.calculate_runoff(test_rainfall, soil_type='medium')
    print(f"   • Calculated Runoff: {runoff:.2f} mm")
    
    water_level = simulator.calculate_water_level(runoff)
    print(f"   • Estimated Water Level: {water_level:.2f} m")
    
    risk_level, risk_num = simulator.classify_flood_risk(water_level, test_rainfall)
    print(f"   • Risk Classification: {risk_level} (Level {risk_num})")
    
    print("\n" + "="*70)
    print("✅ All processing complete! Dashboard ready to use.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
