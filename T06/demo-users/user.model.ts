// Define the User model and its schema using Drizzle ORM and Elysia

import { sql } from 'drizzle-orm';
import { int, sqliteTable, text } from 'drizzle-orm/sqlite-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-typebox';
import { t } from 'elysia';

export const usersTable = sqliteTable('users', {
	id: int().primaryKey({ autoIncrement: true }),
	email: text().notNull().unique(),
	username: text().notNull().unique(),
	password: text().notNull(),
	first_name: text().notNull(),
	last_name: text().notNull(),
	dob: text(),
	role: text('role', { enum: ['admin', 'operator', 'user'] })
		.notNull()
		.default('user'),
	created_at: text()
		.notNull()
		.default(sql`CURRENT_TIMESTAMP`),
	updated_at: text()
		.notNull()
		.default(sql`(CURRENT_TIMESTAMP)`)
		.$onUpdate(() => sql`(CURRENT_TIMESTAMP)`),
});

export const userAddressTable = sqliteTable('user_address', {
	id: int().primaryKey({ autoIncrement: true }),
	user_id: int()
		.notNull()
		.references(() => usersTable.id, { onDelete: 'cascade' }),
	address: text().notNull(),
	phone: text().notNull(),
	state: text().notNull(),
	postal_code: text(),
	country: text().notNull(),
	is_default: int().notNull().default(0),
	created_at: text()
		.notNull()
		.default(sql`CURRENT_TIMESTAMP`),
	updated_at: text()
		.notNull()
		.default(sql`(CURRENT_TIMESTAMP)`)
		.$onUpdate(() => sql`(CURRENT_TIMESTAMP)`),
});

export const schema = { usersTable, userAddressTable } as const;

export const SignUpSchema = createInsertSchema(usersTable, {
	email: t.String({ format: 'email' }),
	username: t.String({ minLength: 5, maxLength: 30 }),
	password: t.String({ minLength: 6 }),
	first_name: t.String({ minLength: 1, maxLength: 50 }),
	last_name: t.String({ minLength: 1, maxLength: 50 }),
	dob: t.Optional(
		t.Union([t.String({ format: 'date' }), t.Null(), t.String({ minLength: 0 })], {
			default: null,
		}),
	),
});

export const UserAddressSchema = createInsertSchema(userAddressTable, {
	address: t.String({ minLength: 5, maxLength: 255 }),
	phone: t.String({ maxLength: 10, format: '^[0-9]{10,11}$' }),
	state: t.String({ maxLength: 100 }),
	postal_code: t.Optional(t.Union([t.String({ maxLength: 20 }), t.Null()])),
	country: t.String({ maxLength: 100 }),
	is_default: t.Optional(t.Integer({ minimum: 0, maximum: 1, default: 0 })),
});

export const UserUpdateSchema = t.Object({
	email: t.Optional(t.String({ format: 'email' })),
	username: t.Optional(t.String({ minLength: 5, maxLength: 30 })),
	first_name: t.Optional(t.String({ minLength: 1, maxLength: 50 })),
	last_name: t.Optional(t.String({ minLength: 1, maxLength: 50 })),
	dob: t.Optional(t.Union([t.String({ format: 'date' }), t.Null()])),
});

export const LoginSchema = t.Object({
	email: t.String({ format: 'email' }),
	password: t.String({ minLength: 6 }),
});

export const UserResponseSchema = createSelectSchema(usersTable);
export const SafeUserResponseSchema = t.Omit(UserResponseSchema, ['password']);
export const UserAddressResponseSchema = createSelectSchema(userAddressTable);
export type Table = typeof usersTable;
