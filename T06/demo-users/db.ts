import { createClient } from '@libsql/client';
import { drizzle } from 'drizzle-orm/libsql';
import { schema } from './user.model';
import 'dotenv/config';

const client = createClient({
	url: process.env.TURSO_USERS_DATABASE_URL as string,
	authToken: process.env.TURSO_USERS_AUTH_TOKEN,
});

export const db = drizzle(client, { schema });
