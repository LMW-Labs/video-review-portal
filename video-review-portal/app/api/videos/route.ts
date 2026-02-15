import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';

export async function GET() {
  try {
    const csvPath = path.join(process.cwd(), 'data', 'videos_for_review.csv');
    if (!fs.existsSync(csvPath)) {
        return NextResponse.json({ error: 'CSV file not found' }, { status: 404 });
    }
    const fileContent = fs.readFileSync(csvPath, 'utf8');
    
    const records = parse(fileContent, {
      columns: true,
      skip_empty_lines: true,
    });

    return NextResponse.json(records);
  } catch (error) {
    console.error('Error reading CSV:', error);
    return NextResponse.json({ error: 'Failed to read video data' }, { status: 500 });
  }
}
