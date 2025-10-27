import { hash, verify } from 'argon2';

export const hashPassword = async (password: string) => {
	return await hash(password);
};

/**
 * Compare a plaintext password with an Argon2 hashed password.
 *
 * @param hashed - The Argon2 hashed password to verify against.
 * @param plain - The plaintext password provided by the user.
 * @returns Promise<boolean> - Resolves to true if the plaintext matches the hash, otherwise false.
 * @throws Error - Propagates errors from argon2.verify (for example, if the provided hash is malformed).
 */
export const comparePassword = async (hashed: string, plain: string) => {
	return await verify(hashed, plain);
};
