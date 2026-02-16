import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import { stringify } from 'csv-stringify/sync';

export async function POST(request: Request) {
  try {
    const { filename, decision, category, notes } = await request.json();
    const csvPath = path.join(process.cwd(), 'data', 'videos_for_review.csv');
    
    if (!fs.existsSync(csvPath)) {
      return NextResponse.json({ error: 'CSV file not found' }, { status: 404 });
    }

    const fileContent = fs.readFileSync(csvPath, 'utf8');
    const records = parse(fileContent, { columns: true, skip_empty_lines: true });

    const updatedRecords = records.map((record: any) => {
      if (record.filename === filename) {
        return {
          ...record,
          reviewer_decision: decision,
          reviewer_category: category || record.reviewer_category,
          reviewer_notes: notes || record.reviewer_notes,
        };
      }
      return record;
    });

    const output = stringify(updatedRecords, { header: true });
    fs.writeFileSync(csvPath, output);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error updating CSV:', error);
    return NextResponse.json({ error: 'Failed to update video data' }, { status: 500 });
  }
}
